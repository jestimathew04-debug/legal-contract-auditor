import re
import os
import pypdf
import risk_rules

# Optional Hugging Face imports
try:
    import torch
    from transformers import AutoTokenizer, AutoModel
    import torch.nn.functional as F
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

class HybridNLPEngine:
    def __init__(self):
        self.has_bert = False
        self.tokenizer = None
        self.model = None
        self.model_name = "nlpaueb/legal-bert-base-uncased"
        
        # Try to initialize Legal-BERT if transformers are installed
        if HAS_TRANSFORMERS:
            try:
                # Set low timeout for model download/load to prevent hanging
                # We also check if we can load it.
                print(f"Transformers detected. Attempting to load local {self.model_name}...")
                # We load tokenizer and model. If we are offline and it's not cached, it will throw an error and fall back.
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, local_files_only=False)
                self.model = AutoModel.from_pretrained(self.model_name, local_files_only=False)
                self.has_bert = True
                print("Legal-BERT loaded successfully!")
            except Exception as e:
                print(f"Could not load Legal-BERT (using offline heuristic engine instead). Detail: {e}")
        else:
            print("Transformers not installed. Running in pure Heuristic mode.")

    def get_status(self):
        """Returns the current state of the NLP engine."""
        return {
            "has_transformers_installed": HAS_TRANSFORMERS,
            "bert_model_loaded": self.has_bert,
            "active_engine": "Legal-BERT + Heuristics" if self.has_bert else "Heuristic Rule-Base Engine"
        }

    def extract_text(self, file_path, file_extension):
        """Extracts text from PDF or TXT files."""
        if file_extension.lower() == '.pdf':
            text = ""
            with open(file_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        elif file_extension.lower() in ['.txt', '.md']:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        else:
            raise ValueError(f"Unsupported file extension: {file_extension}")

    def get_embeddings(self, sentences):
        """Generates embeddings using Legal-BERT if loaded, else returns empty."""
        if not self.has_bert or not sentences:
            return None
        try:
            inputs = self.tokenizer(sentences, padding=True, truncation=True, return_tensors="pt", max_length=512)
            with torch.no_grad():
                outputs = self.model(**inputs)
            # Use mean pooling of token embeddings
            attention_mask = inputs['attention_mask']
            token_embeddings = outputs[0]
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
            sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
            embeddings = sum_embeddings / sum_mask
            return F.normalize(embeddings, p=2, dim=1)
        except Exception as e:
            print(f"Error computing BERT embeddings: {e}")
            return None

    def segment_text(self, text):
        """
        Segments text into paragraphs and records character offsets (start, end).
        This preserves empty lines and formatting for the frontend viewer.
        """
        paragraphs = []
        # Split by double newline or single newline followed by a number/heading
        # We use re.finditer to get offsets of paragraphs
        # Paragraphs are defined as non-empty blocks of text
        pattern = r"([^\n]+(?:\n[^\n]+)*)"
        for match in re.finditer(pattern, text):
            p_text = match.group(0).strip()
            if p_text:
                paragraphs.append({
                    "text": p_text,
                    "start": match.start(),
                    "end": match.end()
                })
        return paragraphs

    def analyze_contract(self, text):
        """
        Analyzes a contract text. Segments the document, classifies clauses,
        audits risks, computes an overall compliance score, and returns results.
        """
        paragraphs = self.segment_text(text)
        analyzed_clauses = []
        high_risk_count = 0
        medium_risk_count = 0
        low_risk_count = 0
        
        # Track paragraphs classified as clauses
        for p in paragraphs:
            clause_key = risk_rules.classify_text(p["text"])
            if clause_key:
                risk_level, issues = risk_rules.audit_clause(clause_key, p["text"])
                
                # Count risk levels
                if risk_level == "HIGH":
                    high_risk_count += 1
                elif risk_level == "MEDIUM":
                    medium_risk_count += 1
                else:
                    low_risk_count += 1
                
                analyzed_clauses.append({
                    "category": risk_rules.CLAUSES[clause_key],
                    "clause_key": clause_key,
                    "text": p["text"],
                    "start": p["start"],
                    "end": p["end"],
                    "risk_level": risk_level,
                    "issues": issues
                })
                
        # Calculate Compliance Score: out of 100
        # Deduct 25 for each high risk issue, 10 for each medium risk issue, up to a minimum of 0
        total_high_issues = sum(len([i for i in c["issues"] if i["severity"] == "HIGH"]) for c in analyzed_clauses)
        total_med_issues = sum(len([i for i in c["issues"] if i["severity"] == "MEDIUM"]) for c in analyzed_clauses)
        
        deductions = (total_high_issues * 25) + (total_med_issues * 10)
        compliance_score = max(0, 100 - deductions)
        
        # If no clauses are found, the compliance score is defaulted to 100 or N/A
        if not analyzed_clauses:
            compliance_score = 100

        # Document classification logic
        doc_type = "General Contract"
        text_lower = text.lower()
        if "non-disclosure" in text_lower or " nda " in text_lower or "confidentiality agreement" in text_lower:
            doc_type = "Non-Disclosure Agreement (NDA)"
        elif "master services" in text_lower or " msa " in text_lower or "services agreement" in text_lower:
            doc_type = "Master Services Agreement (MSA)"
        elif "employment agreement" in text_lower or "employment contract" in text_lower:
            doc_type = "Employment Agreement"
        elif "lease agreement" in text_lower or "rental agreement" in text_lower:
            doc_type = "Lease Agreement"
        elif "license agreement" in text_lower or "software license" in text_lower:
            doc_type = "Software License Agreement"

        return {
            "success": True,
            "raw_text": text,
            "engine_status": self.get_status(),
            "metrics": {
                "total_clauses": len(analyzed_clauses),
                "high_risk_flags": total_high_issues,
                "medium_risk_flags": total_med_issues,
                "compliance_score": compliance_score,
                "document_type": doc_type
            },
            "clauses": analyzed_clauses
        }
