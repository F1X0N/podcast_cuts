# main.py
"""
Pipeline completo: python main.py <URL_DO_EPISÓDIO>
"""
import sys, yaml, os, time, random
from dotenv import load_dotenv
from modules import downloader, transcriber, highlighter, editor, youtube_uploader, moviepy_patch, moviepy_config, outro_appender
from modules.llm_utils import print_llm_report, save_cost_log, save_error_log
from modules.config import load_cfg

from pathlib import WindowsPath

# Aplica o patch do MoviePy
moviepy_patch.patch_resize()

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
            optimization_config
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
        
        if not cfg.get("test_mode", False):
            # Cria descrição com informações do vídeo original
            original_title = video_info.get('title', 'Vídeo Original')
            original_channel = video_info.get('channel', 'Canal Original')
            
            desc = f"""{h.get('description', h.get('hook', ''))}

🎬 Trecho extraído do episódio: "{original_title}"
📺 Canal original: {original_channel}"""
            
            tags_string = " #".join(all_tags)

            desc += f"\n\n{tags_string}"

            # Delay aleatório entre uploads para evitar detecção
            upload_delay_config = cfg.get("upload_delay", {"min_seconds": 3600, "max_seconds": 5400})
            random_time = random.randint(
                upload_delay_config["min_seconds"], 
                upload_delay_config["max_seconds"]
            )
            
            print(f"⏳ Aguardando {random_time//60} minutos antes do upload...")
            time.sleep(random_time)

            youtube_uploader.upload(str(final_clip_path), h["hook"], desc, tags=all_tags)

            print("✔️ Upload concluído")
        else:
            print(f"✔️ Modo de teste: corte gerado em {final_clip_path}")
    
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