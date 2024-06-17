"""
This script provides functionality to download and convert translation models from Hugging Face.
You can download all models or specific models based on language direction.

* Download all models:
    huggingface-cli login 
    python download.py
    
Available translation directions are listed in the 'direct_model_mapping' dictionary.
"""

import os
import shutil
import subprocess
import argparse
from dotenv import load_dotenv

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

# Load environment variables from .env file
load_dotenv()
huggingface_token = os.getenv("HF_TOKEN_READ")
weights_relative_path = os.getenv("MODEL_DIR")


def load_model_names(file_path):
    model_names = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            key, value = line.strip().split("=")
            model_names[key] = value
    return model_names


model_names = load_model_names("model_names.cfg")
direct_model_mapping = {k: f"Eugenememe/{v}" for k, v in model_names.items()}


def download_and_save_model(model_name, model_dir):
    """Downloads a specific model into a directory specified by 'MODEL_DIR' and ensures no duplicates."""
    if not weights_relative_path:
        print(
            "Environment variable 'MODEL_DIR' is not set. Please set 'MODEL_DIR' to the desired base directory for model storage."
        )
        return

    # Check and remove the model directory if it exists to avoid duplicates
    if os.path.exists(model_dir):
        print(
            f"Existing model directory '{model_dir}' found. Deleting to avoid duplicates..."
        )
        shutil.rmtree(model_dir)

    try:
        # Download the tokenizer and model
        print(f"Downloading and saving model '{model_name}' to '{model_dir}'...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_name, use_auth_token=huggingface_token
        )
        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name, use_auth_token=huggingface_token
        )

        # Ensure the model directory exists
        os.makedirs(model_dir, exist_ok=True)

        # Save the tokenizer and model to the specified directory
        tokenizer.save_pretrained(model_dir)
        model.save_pretrained(model_dir)

        print(
            f"Model '{model_name}' successfully downloaded and saved to '{model_dir}'"
        )
    except Exception as e:
        print(f"Error downloading or saving '{model_name}': {e}")


def download_converted_models():
    """Converts all predefined models for optimized inference, skips if model already exists."""
    if not weights_relative_path:
        print(
            "Environment variable 'MODEL_DIR' is not set. Please set 'MODEL_DIR' to the desired base directory for model storage."
        )
        return

    base_command = "ct2-transformers-converter --model {} --output_dir {} --force --copy_files generation_config.json tokenizer_config.json vocab.json source.spm .gitattributes target.spm --quantization float16"

    for model_key, model_path in direct_model_mapping.items():
        model_name = model_path.rsplit("/", maxsplit=1)[-1]

        output_dir = os.path.join(weights_relative_path, f"ct2fast-{model_name}")

        if os.path.exists(output_dir):
            print(
                f"Converted model already exists at: {output_dir}, skipping conversion."
            )
            continue

        command = base_command.format(model_path, output_dir)
        try:
            subprocess.run(command, shell=True, check=True)
            print(f"Conversion completed for model: {model_name}")
        except subprocess.CalledProcessError as e:
            print(f"Error converting model '{model_name}': {e}")

        # Delete the source folder after conversion
        source_dir = os.path.join(weights_relative_path, model_key)

        if os.path.exists(source_dir):
            shutil.rmtree(source_dir)
            print(f"Deleted source folder: {source_dir}")


def download_all_models():
    """Downloads all models specified in the direct_model_mapping."""
    for direction, model_name in direct_model_mapping.items():
        model_dir = os.path.join(weights_relative_path, f"Eugenememe-{direction}")
        if os.path.exists(model_dir):
            print(f"Model '{model_name}' already downloaded (skipping)")
        else:
            download_and_save_model(model_name, model_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download and convert translation models from Hugging Face."
    )
    args = parser.parse_args()

    download_converted_models()
    # download_all_models()
