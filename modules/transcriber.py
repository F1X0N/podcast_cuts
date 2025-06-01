from faster_whisper import WhisperModel

_model = None

def transcribe(video_path: str, model_size: str = "base"):
    """
    Converte fala → texto. Retorna lista de dicionários: {start, end, text}
    """
    global _model
    if _model is None:
        # Usando CPU com otimizações
        _model = WhisperModel(model_size, 
                            device="cpu",
                            compute_type="int8",
                            cpu_threads=8,  # Aumenta o número de threads
                            num_workers=4)  # Usa múltiplos workers
    segments, _ = _model.transcribe(video_path)
    return [{"start": s.start, "end": s.end, "text": s.text} for s in segments]
