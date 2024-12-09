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
    # 将 text 写入 output_file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(text)
    
    print("~~~~~~~~translate success~~~~~")