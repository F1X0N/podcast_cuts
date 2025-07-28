# upload_clips.py
"""
Script de upload para YouTube: python upload_clips.py
Faz upload dos cortes gerados respeitando delays e checkpoints
"""
import sys, time, random
from dotenv import load_dotenv
from modules import youtube_uploader, editor
from modules.llm_utils import print_llm_report, save_cost_log, save_error_log
from modules.config import load_cfg, process_payload_config
from pathlib import Path
from datetime import datetime

load_dotenv()

def run_uploads():
    """Executa o upload de todos os cortes"""
    payload = load_cfg()
    cfgs = process_payload_config(payload)
    
    for cfg in cfgs:
        # Listar todos os diretórios de vídeos em clips/
        base_clips_dir = cfg["paths"]["clips"]
        for video_dir in Path(base_clips_dir).iterdir():
            if not video_dir.is_dir():
                continue
            # Carrega checkpoint de upload do diretório do vídeo
            upload_checkpoint = editor.load_upload_checkpoint(str(video_dir))
            if not upload_checkpoint:
                continue
            generated_clips = upload_checkpoint["generated_clips"]
            episode_url = upload_checkpoint["episode_url"]
            print(f"\n📤 INICIANDO UPLOAD DE {len(generated_clips)} CORTES PARA: {video_dir.name}")
            print("=" * 60)
            # Configurações de delay
            upload_delay_config = cfg.get("upload_delay", {"min_seconds": 1800, "max_seconds": 3600})
            if not cfg.get("upload_mode", False):
                print("⚠️ MODO DE UPLOAD DESATIVADO - Uploads serão simulados")
                print("   Configure upload_mode: true no config.json para upload real")
            uploaded_count = 0
            failed_count = 0
            # Filtra apenas cortes não enviados
            clips_to_upload = [c for c in generated_clips if not c.get("uploaded", False)]
            for i, clip_info in enumerate(clips_to_upload, 1):
                clip_path = clip_info["clip_path"]
                hook = clip_info["hook"]
                description = clip_info["description"]
                tags = clip_info["tags"]
                video_info = clip_info["video_info"]
                print(f"\n📤 Upload {i}/{len(clips_to_upload)}: {hook}")
                print(f"   Arquivo: {Path(clip_path).name}")
                if not Path(clip_path).exists():
                    print(f"   ❌ Arquivo não encontrado: {clip_path}")
                    failed_count += 1
                    continue
                original_title = video_info.get('title', 'Vídeo Original')
                original_channel = video_info.get('channel', 'Canal Original')
                desc = f"""{description}\n\n🎬 Trecho extraído do episódio: \"{original_title}\"\n📺 Canal original: {original_channel}"""
                tags_string = "#" + " #".join(tags)
                desc += f"\n\n{tags_string}"
                try:
                    if cfg.get("upload_mode", True):
                        # Delay antes do upload (exceto para o primeiro)
                        if i > 1:
                            random_time = random.randint(
                                upload_delay_config["min_seconds"], 
                                upload_delay_config["max_seconds"]
                            )
                            print(f"   ⏳ Aguardando {random_time}s antes do upload...")
                            for remaining in range(random_time, 0, -1):
                                minutes = remaining // 60
                                seconds = remaining % 60
                                print(f"\r   ⏳ Aguardando {minutes:02d}:{seconds:02d} antes do upload...", end="", flush=True)
                                time.sleep(1)
                            print()  # Nova linha após a contagem
                        # Faz o upload
                        youtube_uploader.upload(clip_path, hook, desc, tags=tags)
                        print(f"   ✅ Upload concluído")
                        uploaded_count += 1
                        # Marca como enviado
                        clip_info["uploaded"] = True
                        clip_info["uploaded_at"] = datetime.now().isoformat()
                        # Salva checkpoint atualizado
                        editor.save_upload_checkpoint(str(video_dir), episode_url, generated_clips)
                    else:
                        print(f"   🧪 [TESTE] Upload simulado para: {hook}")
                        print(f"   🧪 [TESTE] Descrição: {description[:50]}...")
                        uploaded_count += 1
                        clip_info["uploaded"] = True
                        clip_info["uploaded_at"] = datetime.now().isoformat()
                        editor.save_upload_checkpoint(str(video_dir), episode_url, generated_clips)
                except Exception as e:
                    print(f"   ❌ Erro no upload: {e}")
                    failed_count += 1
                    error_msg = f"Erro no upload do corte {i}: {hook} - {e}"
                    save_error_log(error_msg, episode_url)
            # Resumo final
            print(f"\n" + "=" * 60)
            print(f"📊 RESUMO DO UPLOAD PARA: {video_dir.name}")
            print(f"   • Total de cortes: {len(generated_clips)}")
            print(f"   • Uploads realizados: {uploaded_count}")
            print(f"   • Falhas: {failed_count}")
            # Se todos os cortes foram enviados, remove o checkpoint
            if all(c.get("uploaded", False) for c in generated_clips):
                print(f"   ✅ Todos os uploads concluídos com sucesso!")
                editor.clear_upload_checkpoint(str(video_dir))
            else:
                print(f"   ⚠️ Ainda há cortes não enviados para este vídeo")
            print("=" * 60)

def main():
    """Função principal"""
    try:
        run_uploads()
    except Exception as e:
        import traceback
        save_error_log(traceback.format_exc(), "upload_clips.py")
        print("Erro durante o upload. Veja logs/erros.log para detalhes.")
    finally:
        print_llm_report()
        save_cost_log("upload_clips.py")

if __name__ == "__main__":
    main() 