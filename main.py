import os
import time
from transformers import AutoTokenizer
from flask import Flask, request, jsonify
from flask_cors import CORS
from hf_hub_ctranslate2 import MultiLingualTranslatorCT2fromHfHub
from dotenv import load_dotenv
from hf_hub_ctranslate2 import TranslatorCT2fromHfHub

load_dotenv()

weights_relative_path = os.getenv("MODEL_DIR")
HF_TOKEN = os.getenv("HF_TOKEN_READ")

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


def load_model_names(file_path):
    model_names = {}
    with open(file_path, "r") as f:
        for line in f:
            key, value = line.strip().split("=")
            model_names[key] = value
    return model_names


# Load the base model names from the configuration file
model_names = load_model_names("model_names.cfg")

# Dynamically construct the full model mapping,
direct_model_mapping = {
    k: f"{weights_relative_path}/ct2fast-{v}" for k, v in model_names.items()
}

# Supported languages for intermediate translation
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
    print(
        "The model does not support the 'save_pretrained' method. Please implement a custom saving mechanism."
    )

print(f"Model and tokenizer have been saved to '{model_dir}'")


def translate_text(sentences, src_lang, tgt_lang):
    outputs = model_m2m.generate([sentences], src_lang=[src_lang], tgt_lang=[tgt_lang])
    return outputs[0]


def remove_prompt_from_translation(translated_text):
    parts = translated_text.split(":", 1)
    if len(parts) > 1:
        return parts[1].strip()
    else:
        return translated_text


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


@app.route("/translate", methods=["GET", "POST"])
def translate():
    data = request.get_json()
    try:
        if request.method == "GET":
            original_text = request.args.get("text", "Please input some text")
            source_lang = request.args.get("source_lang", "en")
            target_lang = request.args.get("target_lang", "vi")
        else:  # POST
            original_text = data.get("text", "")
            source_lang = data.get("source_lang", "en")
            target_lang = data.get("target_lang", "vi")

        translated_text = translate_with_timing(original_text, source_lang, target_lang)
        return jsonify(
            {
                "original_text": original_text,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "translated_text": translated_text,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
    app.run(debug=True)
