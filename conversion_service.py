import os
import time
import json
import boto3
import uuid
import re
from threading import Thread
from nltk.tokenize import sent_tokenize
from hf_hub_ctranslate2 import MultiLingualTranslatorCT2fromHfHub, TranslatorCT2fromHfHub
from transformers import AutoTokenizer
from sendmail import send_secure_email  # Ensure this is your function for sending emails
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AWS configuration
AWS_REGION = os.getenv("AWS_REGION")
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
EMAIL = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
sqs = boto3.client('sqs', region_name=AWS_REGION)
s3 = boto3.client('s3', region_name=AWS_REGION)

# Load the base model names from the configuration file
def load_model_names(file_path):
    model_names = {}
    with open(file_path, "r") as f:
        for line in f:
            key, value = line.strip().split("=")
            model_names[key] = value
    return model_names

weights_relative_path = os.getenv("MODEL_DIR")
model_names = load_model_names("model_names.cfg")
direct_model_mapping = {
    k: f"{weights_relative_path}/ct2fast-{v}" for k, v in model_names.items()
}
supported_langs = ["en", "es", "fr", "de", "zh", "vi", "ko", "th", "ja"]
model_name = "michaelfeil_ct2fast-m2m100_1.2B"
model_dir = os.path.join(weights_relative_path, model_name)
os.makedirs(model_dir, exist_ok=True)

# Initialize the model and tokenizer
tokenizer = AutoTokenizer.from_pretrained("facebook/m2m100_1.2B")
model_m2m = MultiLingualTranslatorCT2fromHfHub(
    model_name_or_path="michaelfeil/ct2fast-m2m100_1.2B",
    device="cuda",
    compute_type="int8_float16",
    tokenizer=tokenizer,
)
tokenizer.save_pretrained(model_dir)
if hasattr(model_m2m, "save_pretrained"):
    model_m2m.save_pretrained(model_dir)
else:
    print("The model does not support the 'save_pretrained' method. Please implement a custom saving mechanism.")

print(f"Model and tokenizer have been saved to '{model_dir}'")

# Translation functions
def translate_text(sentences, src_lang, tgt_lang):
    outputs = model_m2m.generate([sentences], src_lang=[src_lang], tgt_lang=[tgt_lang])
    return outputs[0]

def translate_with_timing(text, source_lang, target_lang):
    def perform_translation(text, model_dir):
        start_time = time.time()
        model = TranslatorCT2fromHfHub(
            model_name_or_path=model_dir,
            device="cuda",
            compute_type="int8_float16",
            tokenizer=AutoTokenizer.from_pretrained(model_dir),
        )
        translated_text = model.generate(text=text)
        end_time = time.time()
        return translated_text, end_time - start_time

    if f"{source_lang}-{target_lang}" in ["en-ko", "en-th", "en-ja"]:
        translated_text = translate_text(text, source_lang, target_lang)
        return translated_text

    if f"{source_lang}-{target_lang}" in direct_model_mapping:
        translated_text, time_taken = perform_translation(
            text, direct_model_mapping[f"{source_lang}-{target_lang}"]
        )
        print(
            f"Direct translation time ({source_lang}-{target_lang}): {time_taken:.4f} seconds"
        )
    elif source_lang in supported_langs and target_lang in supported_langs:
        intermediate_text, time_taken_1 = perform_translation(
            text, direct_model_mapping[f"{source_lang}-en"]
        )
        final_text, time_taken_2 = perform_translation(
            intermediate_text, direct_model_mapping[f"en-{target_lang}"]
        )
        translated_text = final_text
        total_time_taken = time_taken_1 + time_taken_2
        print(
            f"2-step translation time ({source_lang}-en-{target_lang}): {total_time_taken:.4f} seconds"
        )
    else:
        translated_text = translate_text(text, source_lang, target_lang)
    return translated_text

# File processing functions
def process_file(file_content, source_lang, target_lang, unique_id, recipient_email):
    sentences = sent_tokenize(file_content)
    translated_sentences = [translate_with_timing(sentence, source_lang, target_lang) for sentence in sentences]
    translated_file_path = f"/tmp/translated_{unique_id}.txt"
    with open(translated_file_path, "w") as file:
        file.write("\n".join(translated_sentences))

    presigned_url = upload_file_to_s3(translated_file_path, S3_BUCKET_NAME, f"translated_{unique_id}.txt")
    
    # Send email notification with the download link
    email_subject = "Your translated file is ready!"
    email_body = f"Your translated file is ready. You can download it from: {presigned_url}"
    send_secure_email(email_subject, email_body, recipient_email, EMAIL, EMAIL_PASSWORD)
    print(f"Email sent to {recipient_email}")

# Function to upload file to S3
def upload_file_to_s3(file_name, bucket_name, object_name=None):
    if object_name is None:
        object_name = file_name
    s3.upload_file(file_name, bucket_name, object_name)
    presigned_url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': object_name}, ExpiresIn=3600)
    return presigned_url

# Function to read message from SQS
def read_message_from_sqs():
    response = sqs.receive_message(
        QueueUrl=SQS_QUEUE_URL,
        AttributeNames=['All'],
        MaxNumberOfMessages=1,
        MessageAttributeNames=['All'],
        VisibilityTimeout=30,
        WaitTimeSeconds=0
    )

    if 'Messages' in response:
        for message in response['Messages']:
            body = message['Body']
            receipt_handle = message['ReceiptHandle']
            sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=receipt_handle)
            return json.loads(body)
    return None

def process_sqs_message():
    while True:
        time.sleep(2)
        message_body = read_message_from_sqs()
        if message_body:
            file_content = message_body['file_content']
            source_lang = message_body['source_lang']
            target_lang = message_body['target_lang']
            unique_id = message_body['unique_id']
            recipient_email = message_body['recipient_email']
            process_file(file_content, source_lang, target_lang, unique_id, recipient_email)

# Start the conversion service
if __name__ == "__main__":
    process_sqs_message()
