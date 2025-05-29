# main.py
"""
Pipeline completo: python main.py <URL_DO_EPISÓDIO>
"""
import sys, yaml, os
from dotenv import load_dotenv
from modules import downloader, transcriber, highlighter, editor, youtube_uploader, thumbnail

load_dotenv()

def load_cfg():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def run(episode_url: str):
    cfg = load_cfg()
    print("Baixando episódio…")
    video = downloader.download(episode_url, cfg["paths"]["raw"])

    print("Transcrevendo…")
    transcript = transcriber.transcribe(str(video), cfg["whisper_size"])

    print("Selecionando highlights…")
    hls = highlighter.find_highlights(transcript, cfg["highlights"])

    for h in hls:
        print(f"Gerando corte: {h['hook']}")
        clip_path = editor.make_clip(str(video), h, transcript, cfg["paths"]["clips"])
        thumb_path = thumbnail.gen_thumbnail(h["hook"])
        desc = f"{h['hook']} | Trecho do podcast original: {episode_url}"
        youtube_uploader.upload(str(clip_path), h["hook"], desc, tags=cfg["tags"])
        print("✔️ Upload concluído\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Uso: python main.py <URL_DO_EPISÓDIO_PODCAST>")
    run(sys.argv[1])