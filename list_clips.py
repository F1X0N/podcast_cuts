#!/usr/bin/env python3
"""
Script utilitário para listar todos os vídeos processados e seus metadados
Uso: python list_clips.py
"""
import json
from pathlib import Path
from modules.editor import list_video_clips
from modules.config import load_cfg

def main():
    cfg = load_cfg()
    clips_dir = cfg["paths"]["clips"]
    
    print("📁 Listando vídeos processados e seus cortes:")
    print("=" * 60)
    
    clips_info = list_video_clips(clips_dir)
    
    if not clips_info:
        print("Nenhum vídeo processado encontrado.")
        return
    
    for video_name, info in clips_info.items():
        print(f"\n🎬 Vídeo: {video_name}")
        print(f"📂 Diretório: {info['video_dir']}")
        
        if info['clips']:
            print(f"🎥 Cortes ({len(info['clips'])}):")
            for clip in info['clips']:
                print(f"   • {clip}")
        
        if info['metadata_files']:
            print(f"📄 Metadados ({len(info['metadata_files'])}):")
            for metadata in info['metadata_files']:
                print(f"   • {metadata}")
                
                # Tenta carregar e mostrar informações básicas do metadata
                try:
                    metadata_path = Path(info['video_dir']) / metadata
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata_data = json.load(f)
                    
                    print(f"     Título: {metadata_data.get('title', 'N/A')}")
                    print(f"     Tags: {', '.join(metadata_data.get('tags', []))}")
                except Exception as e:
                    print(f"     Erro ao carregar metadata: {e}")
        
        print("-" * 40)

if __name__ == "__main__":
    main() 