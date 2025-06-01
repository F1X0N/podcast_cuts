# main.py
"""
Pipeline completo: python main.py <URL_DO_EPISÓDIO>
"""
import sys, yaml, os
from dotenv import load_dotenv
from modules import downloader, transcriber, highlighter, editor, youtube_uploader, thumbnail, moviepy_patch, moviepy_config
from modules.llm_utils import print_llm_report, save_cost_log, save_error_log
from modules.config import load_cfg

# Aplica o patch do MoviePy
moviepy_patch.patch_resize()

load_dotenv()

def run(episode_url: str):
    cfg = load_cfg()
    
    # Tenta carregar checkpoint
    checkpoint = editor.load_checkpoint(cfg["paths"]["clips"])
    if checkpoint:
        print("Checkpoint encontrado! Deseja continuar de onde parou? (s/n)")
        if input().lower() == 's':
            video_path = checkpoint["video_path"]
            transcript = checkpoint["transcript"]
            hls = [checkpoint["highlight"]]  # Processa apenas o highlight do checkpoint
        else:
            editor.clear_checkpoint(cfg["paths"]["clips"])
            checkpoint = None
    
    if not checkpoint:
        print("Baixando episódio…")
        video = downloader.download(episode_url, cfg["paths"]["raw"])
        video_path = str(video)

        print("Transcrevendo…")
        transcript = transcriber.transcribe(video_path, cfg["whisper_size"])

        print("Selecionando highlights…")
        hls = highlighter.find_highlights(transcript, cfg["highlights"])

    for h in hls:
        print(f"\nGerando corte: {h['hook']}")
        # Salva checkpoint antes de processar cada highlight
        editor.save_checkpoint(cfg["paths"]["clips"], video_path, h, transcript)
        
        clip_path = editor.make_clip(video_path, h, transcript, cfg["paths"]["clips"])
        thumb_path = thumbnail.gen_thumbnail(h["hook"])
        
        if not cfg.get("test_mode", False):
            desc = f"{h['hook']} | Trecho do podcast original: {episode_url}"
            youtube_uploader.upload(str(clip_path), h["hook"], desc, tags=cfg["tags"])
            print("✔️ Upload concluído")
        else:
            print(f"✔️ Modo de teste: corte gerado em {clip_path}")
    
    # Limpa o checkpoint após processar todos os highlights
    editor.clear_checkpoint(cfg["paths"]["clips"])
    print("\nProcessamento concluído!")

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