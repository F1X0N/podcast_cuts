# main.py
"""
Pipeline de geração de cortes: python main.py
Processa múltiplos vídeos baseado na configuração do config.json
Gera todos os cortes e salva checkpoint para upload posterior
"""
import sys, json, os
from dotenv import load_dotenv
from modules import downloader, transcriber, highlighter, editor, moviepy_patch, moviepy_config, outro_appender
from modules.llm_utils import print_llm_report, save_cost_log, save_error_log
from modules.config import load_cfg, process_payload_config
from upload_clips import run_uploads

from pathlib import WindowsPath

# Aplica os patches do MoviePy
moviepy_patch.apply_all_patches()

load_dotenv()

def process_single_video(episode_url: str, cfg: dict):
    """
    Processa um único vídeo com a configuração fornecida
    """
    print(f"\n🎬 Processando vídeo: {episode_url}")
    print(f"   • Tags: {cfg.get('tags', [])}")
    print(f"   • Highlights: {cfg.get('highlights', 1)}")
    print(f"   • Velocidade: {cfg.get('content_speed', 1.25)}x")
    print(f"   • Duração: {cfg.get('video_duration', 61)}s")

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
    editor.save_upload_checkpoint(str(video_dir), episode_url, generated_clips)
    
    # Limpa o checkpoint de processamento
    editor.clear_checkpoint(cfg["paths"]["clips"])
    
    print(f"\n🎉 Processamento do vídeo concluído!")
    print(f"   • {len(generated_clips)} cortes gerados")
    print(f"   • Checkpoint salvo para upload posterior")
    
    return generated_clips

def run():
    """
    Processa todos os vídeos configurados no payload
    """
    # Carrega configuração
    payload = load_cfg()
    
    # Processa o payload para obter configurações de cada vídeo
    video_configs = process_payload_config(payload)
    
    print(f"🚀 Iniciando processamento de {len(video_configs)} vídeo(s)")
    print("=" * 60)
    
    all_generated_clips = []
    
    for i, video_cfg in enumerate(video_configs, 1):
        try:
            print(f"\n📹 Vídeo {i}/{len(video_configs)}")
            print("-" * 40)
            
            episode_url = video_cfg["input_url"]
            generated_clips = process_single_video(episode_url, video_cfg)
            all_generated_clips.extend(generated_clips)
            
        except Exception as e:
            import traceback
            print(f"❌ Erro ao processar vídeo {i}: {e}")
            save_error_log(traceback.format_exc(), video_cfg.get("input_url", "URL_DESCONHECIDA"))
            continue
    
    print(f"\n🎉 Processamento completo!")
    print(f"   • Total de vídeos processados: {len(video_configs)}")
    print(f"   • Total de cortes gerados: {len(all_generated_clips)}")
    print(f"   • Execute 'python upload_clips.py' para fazer upload")

    # Executa uploads se configurado
    if payload.get("system_configuration", {}).get("upload_mode", False):
        print("\n📤 Iniciando uploads...")
        run_uploads()

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        import traceback
        save_error_log(traceback.format_exc(), "ERRO_GERAL")
        print("Erro durante o processamento. Veja logs/erros.log para detalhes.")
    finally:
        print_llm_report()
        save_cost_log("PROCESSAMENTO_MULTIPLO")

import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)