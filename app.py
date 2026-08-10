import os
import tempfile
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from nlp_engine import HybridNLPEngine

# Initialize Flask app
app = Flask(__name__)
# Enable Cross-Origin Resource Sharing (CORS) for all routes
CORS(app)

# Limit file uploads to 16MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.md'}

# Initialize the NLP Engine globally so it loads once at startup
print("Initializing Hybrid NLP Engine...")
nlp_engine = HybridNLPEngine()
print("Flask server ready.")

def allowed_file(filename):
    _, ext = os.path.splitext(filename)
    return ext.lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Renders the main SPA dashboard UI."""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint to verify server status and model load state."""
    status_info = nlp_engine.get_status()
    return jsonify({
        "status": "healthy",
        "service": "Legal Contract Clause Extractor & Risk Auditor API",
        "engine": status_info
    })

@app.route('/api/sample', methods=['GET'])
def get_sample():
    """Returns the analysis of the default sample contract."""
    sample_path = os.path.join(os.path.dirname(__file__), 'sample_contract.txt')
    if not os.path.exists(sample_path):
        return jsonify({
            "success": False,
            "error": "Sample contract file not found. Ensure sample_contract.txt is present."
        }), 404
        
    try:
        with open(sample_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        analysis = nlp_engine.analyze_contract(text)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to analyze sample contract: {str(e)}"
        }), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_file():
    """
    Endpoint to upload a legal contract (.pdf or .txt) and analyze it.
    Can also accept a raw 'text' string in JSON body if uploaded directly.
    """
    # Check if raw text is sent in json body
    if request.is_json:
        data = request.get_json()
        raw_text = data.get("text", "")
        if not raw_text.strip():
            return jsonify({"success": False, "error": "Empty text provided"}), 400
        try:
            analysis = nlp_engine.analyze_contract(raw_text)
            return jsonify(analysis)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # Otherwise, check for file upload
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part in the request"}), 400
        
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"}), 400
        
    if not allowed_file(file.filename):
        return jsonify({
            "success": False, 
            "error": f"Unsupported file type. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
        }), 400
        
    try:
        # Create a temporary file to save the upload
        filename = secure_filename(file.filename)
        _, ext = os.path.splitext(filename)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name
            
        try:
            # Extract text from temporary file
            text = nlp_engine.extract_text(temp_path, ext)
            if not text.strip():
                return jsonify({
                    "success": False,
                    "error": "No readable text found in the document. It might be scanned or empty."
                }), 400
                
            # Perform NLP audit
            analysis = nlp_engine.analyze_contract(text)
            analysis["filename"] = filename
            return jsonify(analysis)
            
        finally:
            # Cleanup temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"An error occurred during parsing or analysis: {str(e)}"
        }), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"success": False, "error": "File size exceeds the 16MB limit"}), 413

if __name__ == '__main__':
    # Start Flask development server on port 5000
    app.run(host='127.0.0.1', port=5000, debug=True)
