# upload_clips.py
"""
Script de upload para YouTube: python upload_clips.py
Faz upload dos cortes gerados respeitando delays e checkpoints
"""
import sys, time, random
from dotenv import load_dotenv
from modules import youtube_uploader, editor
from modules.llm_utils import print_llm_report, save_cost_log, save_error_log
from modules.config import load_cfg
from pathlib import Path

load_dotenv()

def run_uploads():
    """Executa o upload de todos os cortes"""
    cfg = load_cfg()
    
    # Carrega checkpoint de upload
    upload_checkpoint = editor.load_upload_checkpoint(cfg["paths"]["clips"])
    
    if not upload_checkpoint:
        print("❌ Nenhum checkpoint de upload encontrado!")
        print("   Execute 'python main.py <URL>' primeiro para gerar os cortes")
        return
    
    generated_clips = upload_checkpoint["generated_clips"]
    episode_url = upload_checkpoint["episode_url"]
    
    print(f"📤 INICIANDO UPLOAD DE {len(generated_clips)} CORTES")
    print("=" * 60)
    
    # Configurações de delay
    upload_delay_config = cfg.get("upload_delay", {"min_seconds": 1800, "max_seconds": 3600})
    
    if cfg.get("test_mode", False):
        print("⚠️ MODO DE TESTE ATIVO - Uploads serão simulados")
        print("   Configure test_mode: false no config.yaml para upload real")
    
    uploaded_count = 0
    failed_count = 0
    
    for i, clip_info in enumerate(generated_clips, 1):
        clip_path = clip_info["clip_path"]
        hook = clip_info["hook"]
        description = clip_info["description"]
        tags = clip_info["tags"]
        video_info = clip_info["video_info"]
        
        print(f"\n📤 Upload {i}/{len(generated_clips)}: {hook}")
        print(f"   Arquivo: {Path(clip_path).name}")
        
        # Verifica se o arquivo existe
        if not Path(clip_path).exists():
            print(f"   ❌ Arquivo não encontrado: {clip_path}")
            failed_count += 1
            continue
        
        # Cria descrição completa
        original_title = video_info.get('title', 'Vídeo Original')
        original_channel = video_info.get('channel', 'Canal Original')
        
        desc = f"""{description}

🎬 Trecho extraído do episódio: "{original_title}"
📺 Canal original: {original_channel}"""

        tags_string = " #".join(tags)
        desc += f"\n\n{tags_string}"
        
        try:
            if not cfg.get("test_mode", False):
                # Delay antes do upload (exceto para o primeiro)
                if i > 1:
                    random_time = random.randint(
                        upload_delay_config["min_seconds"], 
                        upload_delay_config["max_seconds"]
                    )
                    minutes = random_time // 60
                    seconds = random_time % 60
                    
                    print(f"   ⏳ Aguardando {minutes}min {seconds}s antes do upload...")
                    time.sleep(random_time)
                
                # Faz o upload
                youtube_uploader.upload(clip_path, hook, desc, tags=tags)
                print(f"   ✅ Upload concluído")
                uploaded_count += 1
                
            else:
                # Modo de teste - simula upload
                print(f"   🧪 [TESTE] Upload simulado para: {hook}")
                print(f"   🧪 [TESTE] Descrição: {description[:50]}...")
                uploaded_count += 1
                
        except Exception as e:
            print(f"   ❌ Erro no upload: {e}")
            failed_count += 1
            
            # Salva erro no log
            error_msg = f"Erro no upload do corte {i}: {hook} - {e}"
            save_error_log(error_msg, episode_url)
    
    # Resumo final
    print(f"\n" + "=" * 60)
    print(f"📊 RESUMO DO UPLOAD")
    print(f"   • Total de cortes: {len(generated_clips)}")
    print(f"   • Uploads realizados: {uploaded_count}")
    print(f"   • Falhas: {failed_count}")
    
    if failed_count == 0:
        print(f"   ✅ Todos os uploads concluídos com sucesso!")
        # Remove checkpoint após sucesso total
        editor.clear_upload_checkpoint(cfg["paths"]["clips"])
    else:
        print(f"   ⚠️ {failed_count} upload(s) falharam")
        print(f"   • Checkpoint mantido para retry posterior")
    
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