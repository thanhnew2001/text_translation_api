## Translation API

This API allows users to translate text between various language pairs using pre-trained models.

### Running the API

1. **Start the Flask Server**

   ```sh
   python app.py
   ```

2. **API Endpoints**

   - **Translate Text**

     - **GET Request**

       ```
       GET /translate?text=<your-text>&source_lang=<source-language-code>&target_lang=<target-language-code>
       ```

       Example:

       ```sh
       curl -X GET "http://127.0.0.1:5000/translate?text=Hello%20world&source_lang=en&target_lang=vi"
       ```

     - **POST Request**

       ```
       POST /translate
       ```

       Body (JSON):

       ```json
       {
         "text": "Hello world",
         "source_lang": "en",
         "target_lang": "vi"
       }
       ```

       Example:

       ```sh
       curl -X POST "http://127.0.0.1:5000/translate" -H "Content-Type: application/json" -d '{"text": "Hello world", "source_lang": "en", "target_lang": "vi"}'
       ```

   - **Fetch Supported Languages**

     ```
     GET /supported_langs
     ```

     Example:

     ```sh
     curl -X GET "http://127.0.0.1:5000/supported_langs"
     ```

### Example Responses

- **Translate Text Response**

  ```json
  {
    "original_text": "Hello world",
    "source_lang": "en",
    "target_lang": "vi",
    "translated_text": "Xin chào thế giới"
  }
  ```

- **Supported Languages Response**

  ```json
  [
    {"name": "German", "code": "de"},
    {"name": "English", "code": "en"},
    {"name": "Spanish", "code": "es"},
    {"name": "French", "code": "fr"},
    {"name": "Japanese", "code": "ja"},
    {"name": "Korean", "code": "ko"},
    {"name": "Thai", "code": "th"},
    {"name": "Vietnamese", "code": "vi"},
    {"name": "Chinese", "code": "zh"}
  ]
  ```
