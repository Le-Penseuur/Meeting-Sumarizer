import os
import requests
from gradio_web import gradio_web_app 

OLLAMA_SERVER_URL = "http://localhost:11434"  # Replace this with your actual Ollama server URL if different
TRANSLATE_MODEL_DIR = "models"


def get_available_models() -> list[str]:
    """
    Retrieves a list of all available models from the Ollama server and extracts the model names.

    Returns:
        A list of model names available on the Ollama server.
    """
    response = requests.get(f"{OLLAMA_SERVER_URL}/api/tags")
    if response.status_code == 200:
        models = response.json()["models"]
        llm_model_names = [model["model"] for model in models]  # Extract model names
        return llm_model_names
    else:
        raise Exception(
            f"Failed to retrieve models from Ollama server: {response.text}"
        )

def get_available_translate_models() -> list[str]:
    """
    Retrieves a list of available models based on directories in the ./models directory.

    Returns:
        A list of available model names.
    """

    # Get the list of directories in the models directory
    model_dirs = [d for d in os.listdir(TRANSLATE_MODEL_DIR) if os.path.isdir(os.path.join(TRANSLATE_MODEL_DIR, d))]

    # Remove any potential duplicates
    translate_models = list(set(model_dirs))

    return translate_models

# Main function to launch the Gradio interface
if __name__ == "__main__":
    # Retrieve available models for Gradio dropdown input
    ollama_models = get_available_models()  # Retrieve models from Ollama server
    transcription_models = get_available_translate_models()  # Dynamically detect downloaded models

    demo = gradio_web_app(transcription_models, ollama_models, OLLAMA_SERVER_URL)
    demo.create_demo().queue().launch()
