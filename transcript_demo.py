from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess

model_dir = "models/SenseVoiceSmall"

def sensevoice_small_translate(audio_file_path: str, output_file: str):
    model = AutoModel(
        model=model_dir,
        trust_remote_code=True,
        remote_code="./model.py",  
        vad_model="fsmn-vad",
        vad_kwargs={"max_single_segment_time": 30000},
        device="cuda:0",
    )

    # en
    res = model.generate(
        input=f"{audio_file_path}",
        cache={},
        language="auto",  # "zn", "en", "yue", "ja", "ko", "nospeech"
        use_itn=True,
        batch_size_s=60,
        merge_vad=True,  #
        merge_length_s=15,
    )

    text = rich_transcription_postprocess(res[0]["text"])

    # 设置每行的最大长度
    max_line_length = 1024  # 你可以根据需要调整这个值
    
    # 将 text 切割成固定长度的行
    wrapped_text = wrap_text(text, max_line_length)

    # 将 text 写入 output_file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(wrapped_text)
    
    print("~~~~~~~~translate success~~~~~")

def wrap_text(text: str, max_line_length: int) -> str:
    """
    Wraps the given text into lines of a specified maximum length.
    
    Args:
        text (str): The input text to be wrapped.
        max_line_length (int): The maximum length of each line.
    
    Returns:
        str: The wrapped text with each line not exceeding the specified length.
    """
    words = text.split()
    wrapped_lines = []
    current_line = []

    for word in words:
        if len(' '.join(current_line) + ' ' + word) <= max_line_length:
            current_line.append(word)
        else:
            wrapped_lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        wrapped_lines.append(' '.join(current_line))
    
    return '\n'.join(wrapped_lines)