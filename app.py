import logging
import os, json

from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content

app = Flask(__name__)
# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Configure the API key for Google Generative AI (replace with your actual key)
genai.configure(api_key="YOUR_API_KEY")

# Define the model configuration
generation_config = {
    "temperature": 0,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_schema": content.Schema(
        type=content.Type.OBJECT,
        properties={
            "response": content.Schema(
                type=content.Type.OBJECT,
                properties={
                    "grammar_score": content.Schema(type=content.Type.NUMBER),
                    "accuracy_score": content.Schema(type=content.Type.NUMBER),
                    "writing_style_score": content.Schema(type=content.Type.NUMBER),
                },
            ),
        },
    ),
    "response_mime_type": "application/json",
}

# Initialize the model
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    generation_config=generation_config,
    system_instruction="given the image of the homework of a student, evaluate it and give it a score from 0-10 based on accuracy, writing style and grammar. ",
)

# Helper function to upload files to Gemini
def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini."""
    try:
        file = genai.upload_file(path, mime_type=mime_type)
        return file
    except Exception as e:
        raise ValueError(f"Failed to upload file: {e}")

from google.cloud import firestore

# The `project` parameter is optional and represents which project the client
# will act on behalf of. If not supplied, the client falls back to the default
# project inferred from the environment.
db = firestore.Client(project="jamsa-444506")

def save_data(data):
    # currently this gets data, TODO: change to save data
    #docs = db.collection("save_data").stream()
    db.collection("save_data").document().set({"data": data})
    #for doc in docs:
    #    print(f"{doc.id} => {doc.to_dict()}")

    #db.collection("save_data").document().set({"data": Json})
    #logging.info("Evaluation data saved successfully.")
  #except Exception as e:
    #logging.error(f"Error saving data: {str(e)}")

@app.route('/evaluate_homework', methods=['POST'])
def evaluate_homework():
    """Endpoint to evaluate homework from an uploaded image."""
    try:
        # Get the file from the request
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        files = request.files.getlist('file')  # Get all uploaded files

        # Check for multiple files
        if len(files) > 1:
            return jsonify({"error": "Only one file upload is allowed"}), 400

        file = files[0]  # Access the first file if only one uploaded
        mime_type = file.mimetype

        # Save the file temporarily
        temp_path = f"/tmp/{file.filename}"
        file.save(temp_path)

        logging.info(f"Uploaded file: {file.filename}")

        # Upload the file to Gemini
        uploaded_file = upload_to_gemini(temp_path, mime_type=mime_type)

        # Start a chat session with the uploaded file
        chat_session = model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [uploaded_file],
                },
            ]
        )

        logging.info("Sending request to Gemini...")
        response = chat_session.send_message("Evaluate the homework.")
        logging.info("Received response from Gemini:")
        logging.info(response.text)
        save_data(response.text)
        # Return the response as JSON
        return jsonify(response.text), 200

    except Exception as e:
        logging.error(f"Error evaluating homework: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/')
def home():
    return  render_template("index.html")

    # return "Welcome to the Homework Evaluation Service!"


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
