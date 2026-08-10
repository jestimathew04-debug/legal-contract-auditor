# LEXAUDIT — Legal Contract Clause Extractor & Risk Auditor

LEXAUDIT is a production-ready, local, offline web application designed to parse legal contracts (.pdf, .txt, .md), extract critical clauses (Indemnification, Limitation of Liability, Termination, Confidentiality, Governing Law), audit legal risks, and provide actionable compliance recommendations.

Developed with a modern, high-contrast **Black & Red theme** executive dashboard, the app operates entirely on-device, ensuring complete privacy with zero external API calls.

---

## 🛠️ Tech Stack & Architecture

- **Backend**: Python 3.10+ with Flask & CORS support.
- **NLP Engine**: Hybrid Heuristic parser with optional Hugging Face `nlpaueb/legal-bert-base-uncased` integration.
- **Document Parsing**: `pypdf` for extracting text streams from PDF files.
- **Frontend**: Single Page Application (SPA) designed with HTML5, vanilla ES6 JavaScript (Fetch API), and Tailwind CSS (CDN).

---

## 🚀 Quick Start Guide

The server is currently running in the background. You can open and view the application by visiting:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

If you need to manually stop and restart the application, follow the steps below:

### 1. Prerequisite Checks
Ensure Python 3.10+ is installed on your machine.

### 2. Activate the Virtual Environment
Open PowerShell in the project directory and run:
```powershell
# Activate the virtual environment
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies (If setting up on a new workspace)
```powershell
pip install -r requirements.txt
```

### 4. Start the Application
```powershell
python app.py
```
Visit `http://127.0.0.1:5000` in your web browser.

---

## 🧠 Model Configuration & Customization

### Pure Heuristic Mode (Default & Fast)
Out-of-the-box, the app runs in **Heuristic Mode** using optimized regex rules defined in `risk_rules.py`. This executes instantly, uses minimal CPU/memory, and requires no internet connection or large file downloads.

### Activating Legal-BERT Mode
If you wish to enable the local Hugging Face `nlpaueb/legal-bert-base-uncased` model for extracting semantic sentence embeddings:

1. **Install Optional Dependencies**:
   Ensure PyTorch and Hugging Face Transformers are installed in your environment:
   ```powershell
   .venv\Scripts\pip install torch transformers
   ```
2. **Restart the Server**:
   ```powershell
   python app.py
   ```
   Upon startup, the backend will auto-detect the packages and attempt to download the model from Hugging Face. Once cached locally, it runs 100% offline. If the download fails or the machine is offline, it will automatically fall back to the Heuristic engine, ensuring 100% server startup reliability.

---

## 🧪 Testing the Application

To run the automated test suite and verify the classification and risk rules:
```powershell
.venv\Scripts\python.exe C:\Users\mathe\.gemini\antigravity\brain\67229b1c-549b-4c99-9733-c6db89c46a42\scratch\test_app.py
```

---

## 📁 Directory Structure
```
c:\Users\mathe\OneDrive\Desktop\legal model\
├── app.py                   # Flask server, routing, upload handler
├── nlp_engine.py            # Sentence segmenter and hybrid NLP parser
├── risk_rules.py            # Risk rules matching and scoring logic
├── requirements.txt         # Core dependencies
├── sample_contract.txt      # Mock contract text for quick-load testing
├── templates/
│   └── index.html           # SPA Dashboard HTML structure
└── static/
    ├── css/
    │   └── custom.css       # Color-coded risk highlighting & custom styles
    └── js/
        └── app.js           # Fetch logic, UI rendering, offset highlighting, PDF export
```

---

## 📝 License
Proprietary tool built for local administrative legal contract audits.
