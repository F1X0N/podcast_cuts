# transcriber.py
from faster_whisper import WhisperModel

def transcribe(video_path):
    model = WhisperModel("base", device="cuda", compute_type="float16")
    segments, _ = model.transcribe(video_path)
    return [{"start":s.start, "end":s.end, "text":s.text} for s in segments]
