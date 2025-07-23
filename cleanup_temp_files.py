#!/usr/bin/env python3
"""
Script para limpar arquivos temporários que podem estar causando problemas
"""
import os
import tempfile
import glob
import time

def cleanup_temp_files():
    """
    Limpa arquivos temporários que podem estar causando problemas de permissão
    """
    print("🧹 Iniciando limpeza de arquivos temporários...")
    
    # Lista de padrões de arquivos temporários
    temp_patterns = [
        os.path.join(tempfile.gettempdir(), "*.wav"),
        os.path.join(tempfile.gettempdir(), "*.mp4"),
        os.path.join(tempfile.gettempdir(), "*.avi"),
        os.path.join(tempfile.gettempdir(), "*.mov"),
        os.path.join(tempfile.gettempdir(), "tmp*"),
        os.path.join(tempfile.gettempdir(), "temp*"),
    ]
    
    cleaned_count = 0
    
    for pattern in temp_patterns:
        try:
            files = glob.glob(pattern)
            for file_path in files:
                try:
                    # Tenta remover o arquivo
                    if os.path.exists(file_path):
                        os.unlink(file_path)
                        cleaned_count += 1
                        print(f"   ✅ Removido: {os.path.basename(file_path)}")
                except PermissionError:
                    print(f"   ⚠️ Não foi possível remover (em uso): {os.path.basename(file_path)}")
                except Exception as e:
                    print(f"   ❌ Erro ao remover {os.path.basename(file_path)}: {e}")
        except Exception as e:
            print(f"   ❌ Erro ao processar padrão {pattern}: {e}")
    
    print(f"\n🎉 Limpeza concluída! {cleaned_count} arquivos removidos.")
    
    # Força coleta de lixo
    import gc
    gc.collect()
    
    print("♻️ Memória liberada.")

def force_close_moviepy_clips():
    """
    Força o fechamento de clips do MoviePy que possam estar em memória
    """
    print("🎬 Forçando fechamento de clips do MoviePy...")
    
    try:
        import moviepy.editor as mp
        
        # Força limpeza de recursos do MoviePy
        mp.VideoFileClip.close_all_clips()
        print("   ✅ Clips do MoviePy fechados")
    except Exception as e:
        print(f"   ⚠️ Erro ao fechar clips: {e}")

if __name__ == "__main__":
    print("🔧 Utilitário de Limpeza de Arquivos Temporários")
    print("=" * 50)
    
    # Força fechamento de clips
    force_close_moviepy_clips()
    
    # Aguarda um pouco para garantir que os recursos sejam liberados
    print("⏳ Aguardando liberação de recursos...")
    time.sleep(2)
    
    # Limpa arquivos temporários
    cleanup_temp_files()
    
    print("\n✨ Sistema limpo e pronto para uso!") 