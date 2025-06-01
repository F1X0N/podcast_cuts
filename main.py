# main.py
"""
Pipeline completo: python main.py <URL_DO_EPISÓDIO>
"""
import sys, yaml, os
from dotenv import load_dotenv
from modules import downloader, transcriber, highlighter, editor, youtube_uploader, thumbnail, moviepy_patch, moviepy_config
from modules.llm_utils import print_llm_report, save_cost_log, save_error_log

# Aplica o patch do MoviePy
moviepy_patch.patch_resize()

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
        
        if not cfg.get("test_mode", False):
            desc = f"{h['hook']} | Trecho do podcast original: {episode_url}"
            youtube_uploader.upload(str(clip_path), h["hook"], desc, tags=cfg["tags"])
            print("✔️ Upload concluído\n")
        else:
            print(f"✔️ Modo de teste: corte gerado em {clip_path}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Tenta ler a URL do arquivo input_url.txt
        try:
            with open("input_url.txt", "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                if lines:
                    episode_url = lines[0]
                else:
                    sys.exit("Arquivo input_url.txt está vazio.")
        except Exception:
            sys.exit("Uso: python main.py <URL_DO_EPISÓDIO_PODCAST> ou preencha input_url.txt")
    else:
        episode_url = sys.argv[1]
    try:
        run(episode_url)
    except Exception as e:
        import traceback
        save_error_log(traceback.format_exc(), episode_url)
        print("Erro durante o processamento. Veja logs/erros.log para detalhes.")
    finally:
        print_llm_report()
        save_cost_log(episode_url)

import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)