from faster_whisper import WhisperModel

_model = None

def transcribe(video_path: str, model_size: str = "base"):
    """
    Converte fala → texto. Retorna lista de dicionários: {start, end, text}
    """
    global _model
    if _model is None:
        _model = WhisperModel(model_size, device="cuda" if model_size != "tiny" else "cpu",
                              compute_type="float16" if model_size != "tiny" else "int8")
    segments, _ = _model.transcribe(video_path)
    return [{"start": s.start, "end": s.end, "text": s.text} for s in segments]
