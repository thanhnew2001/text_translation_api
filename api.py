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
        
        # Read the file content
        with open(filepath, 'r') as f:
            file_content = f.read()
        
        # Generate a unique ID for this file
        unique_id = str(uuid.uuid4())
<<<<<<< HEAD
        s3_object_key = f"{filename.rsplit('.', 1)[0]}_{unique_id}.{filename.rsplit('.', 1)[1]}"
        
        # Upload the file to S3
        if upload_file_to_s3(filepath, S3_BUCKET_NAME, s3_object_key):
            # Send a message to SQS with the S3 object reference
            message = {
                's3_bucket': S3_BUCKET_NAME,
                's3_key': s3_object_key,
                'unique_id': unique_id,
                'source_lang': request.form.get('source_lang', 'en'),
                'target_lang': request.form.get('target_lang', 'vi')
            }
            
            sqs.send_message(
                QueueUrl=SQS_QUEUE_URL,
                MessageBody=json.dumps(message)
            )
            
            return jsonify({"message": "File uploaded successfully and message sent to queue"}), 200
        else:
            return jsonify({"error": "Failed to upload file to S3"}), 500
=======
        
        # Send a message to SQS with the file content and details
        message = {
            'file_content': file_content,
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
>>>>>>> parent of 52792a4 (upload file to s3)

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
