import os
import json
import boto3
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import uuid 


# Load environment variables
load_dotenv()

# Flask app setup
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Directory where files are saved
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# AWS configuration
AWS_REGION = os.getenv("AWS_REGION")
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")
s3 = boto3.client('s3', region_name=AWS_REGION)
sqs = boto3.client('sqs', region_name=AWS_REGION)

# Allowed extensions
ALLOWED_EXTENSIONS = {'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Flask routes
@app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Generate a unique ID for this file
        unique_id = str(uuid.uuid4())
        
        # Send a message to SQS with the file details
        message = {
            'file_key': filename,
            'unique_id': unique_id,
            'source_lang': request.form.get('source_lang', 'en'),
            'target_lang': request.form.get('target_lang', 'vi'),
            'recipient_email': request.form.get('recipient_email')
        }
        
        sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(message)
        )
        
        return jsonify({"message": "File uploaded successfully and message sent to queue"}), 200

    return jsonify({"error": "File type not allowed"}), 400

@app.route("/supported_langs", methods=["GET"])
def fetch_supported_langs():
    try:
        supported_languages = [
            {"name": "German", "code": "de"},
            {"name": "English", "code": "en"},
            {"name": "Spanish", "code": "es"},
            {"name": "French", "code": "fr"},
            {"name": "Japanese", "code": "ja"},
            {"name": "Korean", "code": "ko"},
            {"name": "Thai", "code": "th"},
            {"name": "Vietnamese", "code": "vi"},
            {"name": "Chinese", "code": "zh"},
        ]
        return jsonify(supported_languages), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5555)
