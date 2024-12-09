# AI-Powered Meeting Summarizer

## Requirements

- Python 3.x
- [FFmpeg](https://www.ffmpeg.org/) (for audio processing)
- [Ollama server](https://ollama.com/) (for text summarization)
- [Gradio](https://www.gradio.app/) (for the web interface)
- [Requests](https://requests.readthedocs.io/en/latest/) (for handling API calls to the Ollama server)

## Pre-Installation

Before running the application, ensure you have Ollama that is running on your local machine or a server. You can follow the instructions provided in the [Ollama repository](https://github.com/ollama/ollama) to set up the server. Do not forget to download and run a model from the Ollama server.

```bash
# To install and run Llama 3.2
curl -fsSL https://ollama.com/install.sh | sh
ollama run qwen2.5:1.5b
```

## Installation

Follow the steps below to set up and run the application:

### Step 1: Clone the Repository and Download SenseVoiceSmall Model

```bash
git clone https://github.com/AlexisBalayre/AI-Powered-Meeting-Summarizer
cd AI-Powered-Meeting-Summarizer
```

### Step 2: Run the Setup Script

To install all necessary dependencies (including Python virtual environment, `whisper.cpp`, FFmpeg, and Python packages), and to run the application, execute the provided setup script:

```bash
chmod +x run_meeting_summarizer.sh
./run_meeting_summarizer.sh
```

This script will:

- Create and activate a Python virtual environment.
- Install necessary Python packages like `requests` and `gradio`.
- Check if `FFmpeg` is installed and install it if missing.
- **Run the `main.py` script**, which will start the Gradio interface for the application.

### Step 3: Accessing the Application

Once the setup and execution are complete, Gradio will provide a URL (typically `http://127.0.0.1:7860`). Open this URL in your web browser to access the Meeting Summarizer interface.

Alternatively, after setup, you can activate the virtual environment and run the Python script manually:

```bash
# Activate the virtual environment
source .venv/bin/activate

# Run the main.py script
python main.py
```
