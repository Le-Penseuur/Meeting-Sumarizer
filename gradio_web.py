import json
import os
import subprocess
import gradio as gr
import requests
import transcript_demo

class gradio_web_app:
    def __init__(self, transcription_models, summary_models, ollama_server_url):
        self.transcription_models = transcription_models
        self.summary_models =summary_models
        self.OLLAMA_SERVER_URL = ollama_server_url

    def create_demo(self):
        with gr.Blocks(title = "Meeting Summarizer") as demo:

            with gr.Row():

                with gr.Column():
                    with gr.Tab("上传音频文件"):
                        # 音频文件传输框
                        audio_box = gr.Audio(type="filepath")
                    with gr.Tab("上传文本文件"):
                        # 转录文件上传框
                        uploadfile_box = gr.File(file_types = ["text"])
                    
                    # 上下文信息输入框
                    context_box = gr.Textbox(
                                label="Context (可选)",
                                placeholder="为纪要提供额外的上下文信息",
                                interactive=True,
                            )
                    # 语音大模型选择框
                    transcription_model_box = gr.Dropdown(
                                choices=self.transcription_models,
                                label="选择一个语音转录的大模型",
                                value=self.transcription_models[0],
                            )
                    # 生成纪要大模型选择框
                    summary_model_box = gr.Dropdown(
                                choices=self.summary_models,
                                label="选择一个生成纪要的大模型",
                                value=self.summary_models[0],
                            )

                    with gr.Row():
                        # 清空按钮
                        clear_button = gr.Button("Clear")
                        # 语音转录按钮
                        transcript_button = gr.Button("Transcript")
                        # 生成纪要按钮
                        summary_button = gr.Button("Generate Summary")

                with gr.Column("transcription"):
                    # 转录文本折叠框
                    with gr.Accordion(label = "transcription"):
                        # 转录文本输出框
                        transcription_output = gr.Textbox(
                                placeholder= "",
                                show_copy_button=True,
                                interactive=True,
                                container = False,
                                lines = 10
                            )
                
                    # 纪要文本输出框
                    summary_output = gr.Textbox(
                            label="Summary",
                            placeholder="Summary will appear here",
                            show_copy_button=True,
                        )
                    # # 下载文件区
                    # downloadfile_box = gr.File(
                    #         file_types = ["text"],
                    #         label="Download Transcription",
                    #     )
            
            # 按钮点击函数  
            clear_button.click(
                fn=self.clear,
                inputs=[],
                outputs=[audio_box, uploadfile_box, context_box, transcription_output, summary_output]
            )
            transcript_button.click(
                fn=self.transcript,
                inputs=[audio_box, transcription_model_box],
                outputs=[transcription_output]
            )
            summary_button.click(
                fn=self.transcription_output_is,
                inputs=[audio_box, uploadfile_box, transcription_model_box, transcription_output],
                outputs=[transcription_output]
            ).then(
                fn=self.summarize_with_model,
                inputs=[context_box, summary_model_box, transcription_output],
                outputs = [summary_output]
            )
            uploadfile_box.upload(
                fn=self.uploadfile,
                inputs=[uploadfile_box],
                outputs=[transcription_output]
            )
        
        return demo 

    def clear(self):
        return [None, None, None, "", "Summary will appear here"]

    def uploadfile(self, uploaded_file):
        # 实现上传文件的逻辑
        if uploaded_file == None:
            return None
        else:
            transcription = ""
            with open(uploaded_file, "r") as f:
                transcription += ''.join(f.readlines())
            return transcription.replace('\n', ' ')
        
    def transcript(self, audio_file_path, transcription_model):
        # 实现转录逻辑
        if audio_file_path == None:
            gr.Warning("未上传音频文件！")
            return None
        if transcription_model == None:
            gr.Warning("未选择语音大模型！")
            return None
    
        output_file = "output.txt"
        transcript = ""

        print("Processing audio file:", audio_file_path)
        gr.Info(f"Processing audio file: {audio_file_path} ")

        # Convert the input file to WAV format if necessary
        output_audio_path = self.preprocess_audio_file(audio_file_path)

        print("Audio preprocessed")
        gr.Info(f"Audio preprocessed")

        if transcription_model == "SenseVoiceSmall":
                 transcript_demo.sensevoice_small_translate(output_audio_path, output_file)
        
        # Read the output from the transcript
        with open(output_file, "r", encoding='utf-8') as f:
            transcript += ''.join(f.readlines())

        # Save the transcript to a downloadable file
        transcript_file = "transcript.txt"
        with open(transcript_file, "w") as transcript_f:
            transcript_f.write(transcript)
        
        os.remove(output_audio_path)

        gr.Info("Transcription complete!")
        return transcript.replace('\n', ' ')

    def transcription_output_is(self, audio_file_path, uploadfile_path, transcription_model, transcription_output:str):
        # 实现转录文本框为空时的操作
        if "" == transcription_output.strip():
            if audio_file_path != None:
                return self.transcript(audio_file_path, transcription_model)
            elif uploadfile_path != None:
                return self.uploadfile(uploadfile_path)
            else:
                gr.Info("Please upload audio/text file!")
                return gr.update("")
        else:
            return gr.update("")    

    def preprocess_audio_file(self, audio_file_path: str) -> str:
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

    def summarize_with_model(self, context: str, llm_model_name: str,text: str) -> str:
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

        if text == "":
            return gr.update()

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
            f"{self.OLLAMA_SERVER_URL}/api/generate", json=data, headers=headers, stream=True
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
