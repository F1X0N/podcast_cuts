# main.py
"""
Pipeline de geração de cortes: python main.py <URL_DO_EPISÓDIO>
Gera todos os cortes e salva checkpoint para upload posterior
"""
import sys, yaml, os
from dotenv import load_dotenv
from modules import downloader, transcriber, highlighter, editor, moviepy_patch, moviepy_config, outro_appender
from modules.llm_utils import print_llm_report, save_cost_log, save_error_log
from modules.config import load_cfg
from upload_clips import run_uploads

from pathlib import WindowsPath

# Aplica os patches do MoviePy
moviepy_patch.apply_all_patches()

load_dotenv()

def run(episode_url: str):
    cfg = load_cfg()

    # Tenta carregar checkpoint com validação da URL do episódio
    checkpoint = editor.validate_checkpoint_for_episode(cfg["paths"]["clips"], episode_url)
    if checkpoint:
        video_path = checkpoint["video_path"]
        transcript = checkpoint["transcript"]
        video_info = checkpoint.get("video_info", {})
        hls = [checkpoint["highlight"]]
        print(f"🔄 Continuando processamento a partir do checkpoint")
    
    if not checkpoint:
        print("Baixando episódio…")
        video, video_info = downloader.download(episode_url, cfg["paths"]["raw"])
        video_path = str(video)
        
        print(f"Vídeo: {video_info.get('title', 'N/A')}")
        print(f"Canal: {video_info.get('channel', 'N/A')}")

        print("Transcrevendo…")
        transcript = transcriber.transcribe(video_path, cfg["whisper_size"])

        print("Selecionando highlights…")
        hls = highlighter.find_highlights(transcript, video_info, cfg["highlights"])

    # Lista para armazenar informações dos cortes gerados
    generated_clips = []

    for h in hls:
        print(f"\nGerando corte: {h['hook']}")
        # Salva checkpoint antes de processar cada highlight, incluindo a URL do episódio
        editor.save_checkpoint(cfg["paths"]["clips"], video_path, h, transcript, video_info, episode_url)
        
        # Configurações de otimização
        optimization_config = cfg.get("video_optimization", {
            "use_gpu": True,
            "quality": "balanced",
            "enable_parallel": True
        })
        
        clip_path = editor.make_clip(
            video_path, 
            h, 
            transcript, 
            cfg["paths"]["clips"], 
            video_info,
            optimization_config,
            cfg.get("content_speed", 1.25),
            cfg.get("preserve_pitch", True),
            cfg.get("video_duration", 61)
        )
        
        # Salva os metadados do corte
        video_dir = clip_path.parent
        clip_filename = clip_path.name
        all_tags = h.get('tags', []) + cfg.get("tags", [])
        editor.save_clip_metadata(video_dir, clip_filename, h, video_info, episode_url, all_tags)

        # Anexa outro ao corte se configurado
        final_clip_path = clip_path
        if cfg.get("append_outro", True):  # Por padrão, anexa outro
            try:
                print("🎬 Anexando outro ao corte...")
                final_clip_path = outro_appender.append_outro(str(clip_path), optimization_config)
                print(f"✅ Outro anexado: {final_clip_path}")
            except Exception as e:
                print(f"⚠️ Erro ao anexar outro: {e}")
                print("   Continuando com o corte original...")
                final_clip_path = clip_path
        
        # Armazena informações do corte para upload posterior
        clip_info = {
            "clip_path": str(final_clip_path),
            "hook": h["hook"],
            "description": h.get('description', h.get('hook', '')),
            "tags": all_tags,
            "video_info": video_info,
            "episode_url": episode_url
        }
        generated_clips.append(clip_info)
        
        print(f"✅ Corte gerado: {final_clip_path}")
    
    # Salva checkpoint de conclusão com todos os cortes gerados
    editor.save_upload_checkpoint(cfg["paths"]["clips"], episode_url, generated_clips)
    
    # Limpa o checkpoint de processamento
    editor.clear_checkpoint(cfg["paths"]["clips"])
    
    print(f"\n🎉 Geração de cortes concluída!")
    print(f"   • {len(generated_clips)} cortes gerados")
    print(f"   • Checkpoint salvo para upload posterior")
    print(f"   • Execute 'python upload_clips.py' para fazer upload")

    run_uploads()

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