import subprocess
import os
import gradio as gr
import requests
import json
import translate

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


def summarize_with_model(llm_model_name: str, context: str, text: str) -> str:
    """
    Uses a specified model on the Ollama server to generate a summary.
    Handles streaming responses by processing each line of the response.

    Args:
        llm_model_name (str): The name of the model to use for summarization.
        context (str): Optional context for the summary, provided by the user.
        text (str): The transcript text to summarize.

    Returns:
        str: The generated summary text from the model.
    """
    prompt = f"""你将被提供了一份会议记录，以及一些可选的背景信息。
    
          背景信息如下: {context if context else 'No additional context provided.'}
    
         会议记录如下:
    
    {text}
    
         请用中文对上述文本进行总结，总结结构如下：
         一、摘要
         xxx
         二 、纪要
         1.xx
         2.xx
         3.xx
    """

    headers = {"Content-Type": "application/json"}
    data = {"model": llm_model_name, "prompt": prompt}

    response = requests.post(
        f"{OLLAMA_SERVER_URL}/api/generate", json=data, headers=headers, stream=True
    )

    if response.status_code == 200:
        full_response = ""
        try:
            # Process the streaming response line by line
            for line in response.iter_lines():
                if line:
                    # Decode each line and parse it as a JSON object
                    decoded_line = line.decode("utf-8")
                    json_line = json.loads(decoded_line)
                    # Extract the "response" part from each JSON object
                    full_response += json_line.get("response", "")
                    # If "done" is True, break the loop
                    if json_line.get("done", False):
                        break
            return full_response
        except json.JSONDecodeError:
            print("Error: Response contains invalid JSON data.")
            return f"Failed to parse the response from the server. Raw response: {response.text}"
    else:
        raise Exception(
            f"Failed to summarize with model {llm_model_name}: {response.text}"
        )


def preprocess_audio_file(audio_file_path: str) -> str:
    """
    Converts the input audio file to a WAV format with 16kHz sample rate and mono channel.

    Args:
        audio_file_path (str): Path to the input audio file.

    Returns:
        str: The path to the preprocessed WAV file.
    """
    output_wav_file = f"{os.path.splitext(audio_file_path)[0]}_converted.wav"

    # Ensure ffmpeg converts to 16kHz sample rate and mono channel
    cmd = f'ffmpeg -y -i "{audio_file_path}" -ar 16000 -ac 1 "{output_wav_file}"'
    subprocess.run(cmd, shell=True, check=True)

    return output_wav_file


def translate_and_summarize(
    audio_file_path: str, context: str, translate_model_name: str, llm_model_name: str
) -> tuple[str, str]:
    """
    Translates the audio file into text using the translation model and generates a summary using Ollama.
    Also provides the transcript file for download.

    Args:
        audio_file_path (str): Path to the input audio file.
        context (str): Optional context to include in the summary.
        translate_model_name (str): model to use for audio-to-text conversion.
        llm_model_name (str): Model to use for summarizing the transcript.

    Returns:
        tuple[str, str]: A tuple containing the summary and the path to the transcript file for download.
    """
    output_file = "output.txt"

    print("Processing audio file:", audio_file_path)

    # Convert the input file to WAV format if necessary
    audio_file_wav = preprocess_audio_file(audio_file_path)

    print("Audio preprocessed:", audio_file_wav)

    #  call the translation module 
    if translate_model_name == "SenseVoiceSmall":
        translate.sensevoice_small_translate(audio_file_wav, output_file)

    # Read the output from the transcript
    with open(output_file, "r") as f:
        transcript = f.read()

    # Save the transcript to a downloadable file
    transcript_file = "transcript.txt"
    with open(transcript_file, "w") as transcript_f:
        transcript_f.write(transcript)

    # Generate summary from the transcript using Ollama's model
    summary = summarize_with_model(llm_model_name, context, transcript)

    # Clean up temporary files
    os.remove(audio_file_wav)
    os.remove(output_file)

    # Return the downloadable link for the transcript and the summary text
    return summary, transcript_file


# Gradio interface
def gradio_app(
    audio, context: str, translate_model_name: str, llm_model_name: str
) -> tuple[str, str]:
    """
    Gradio application to handle file upload, model selection, and summary generation.

    Args:
        audio: The uploaded audio file.
        context (str): Optional context provided by the user.
        translate_model_name (str): The selected translation model name.
        llm_model_name (str): The selected language model for summarization.

    Returns:
        tuple[str, str]: A tuple containing the summary text and a downloadable transcript file.
    """
    return translate_and_summarize(audio, context, translate_model_name, llm_model_name)


# Main function to launch the Gradio interface
if __name__ == "__main__":
    # Retrieve available models for Gradio dropdown input
    ollama_models = get_available_models()  # Retrieve models from Ollama server
    translate_models = (
         get_available_translate_models()
    )  # Dynamically detect downloaded models

    # Ensure the first model is selected by default
    iface = gr.Interface(
        fn=gradio_app,
        inputs=[
            gr.Audio(type="filepath", label="Upload an audio file"),
            gr.Textbox(
                label="Context (optional)",
                placeholder="Provide any additional context for the summary",
            ),
            gr.Dropdown(
                choices=translate_models,
                label="Select a model for audio-to-text conversion",
                value=translate_models[0],
            ),
            gr.Dropdown(
                choices=ollama_models,
                label="Select a model for summarization",
                value=ollama_models[0] if ollama_models else None,
            ),
        ],
        outputs=[
            gr.Textbox(
                label="Summary",
                show_copy_button=True,
            ),  # Display the summary generated by the Ollama model
            gr.File(
                label="Download Transcript"
            ),  # Provide the transcript as a downloadable file
        ],
        analytics_enabled=False,
        title="Meeting Summarizer",
        description="Upload an audio file of a meeting and get a summary of the key concepts discussed.",
    )

    iface.launch(debug=True)
