#!/usr/bin/env python3
"""
Script para verificar status dos checkpoints e cortes
python check_status.py
"""

import os
from pathlib import Path
from modules.config import load_cfg
from modules.editor import load_checkpoint, load_upload_checkpoint

def check_processing_status():
    """Verifica status do processamento"""
    print("🔍 VERIFICANDO STATUS DO SISTEMA")
    print("=" * 50)
    
    cfg = load_cfg()
    clips_dir = Path(cfg["paths"]["clips"])
    
    if not clips_dir.exists():
        print("❌ Diretório de clips não encontrado")
        return
    
    # Verifica checkpoint de processamento
    processing_checkpoint = load_checkpoint(cfg["paths"]["clips"])
    if processing_checkpoint:
        print("🔄 CHECKPOINT DE PROCESSAMENTO ENCONTRADO")
        print(f"   • Vídeo: {Path(processing_checkpoint['video_path']).name}")
        print(f"   • Highlight atual: {processing_checkpoint['highlight']['hook']}")
        print(f"   • URL: {processing_checkpoint.get('episode_url', 'N/A')}")
        print("   • Status: Processamento em andamento")
        print("   • Ação: Execute 'python main.py <URL>' para continuar")
    else:
        print("✅ Nenhum checkpoint de processamento encontrado")
    
    # Verifica checkpoint de upload
    upload_checkpoint = load_upload_checkpoint(cfg["paths"]["clips"])
    if upload_checkpoint:
        print("\n📤 CHECKPOINT DE UPLOAD ENCONTRADO")
        print(f"   • Cortes gerados: {upload_checkpoint['total_clips']}")
        print(f"   • URL: {upload_checkpoint['episode_url']}")
        print("   • Status: Cortes prontos para upload")
        print("   • Ação: Execute 'python upload_clips.py' para fazer upload")
        
        # Lista os cortes
        print("\n📋 Cortes prontos:")
        for i, clip in enumerate(upload_checkpoint['generated_clips'], 1):
            clip_path = Path(clip['clip_path'])
            exists = "✅" if clip_path.exists() else "❌"
            print(f"   {i}. {exists} {clip_path.name} - {clip['hook']}")
    else:
        print("\n✅ Nenhum checkpoint de upload encontrado")
    
    # Lista diretórios de vídeos processados
    print("\n📁 DIRETÓRIOS DE VÍDEOS PROCESSADOS:")
    video_dirs = [d for d in clips_dir.iterdir() if d.is_dir()]
    
    if video_dirs:
        for video_dir in video_dirs:
            print(f"   📂 {video_dir.name}")
            
            # Conta arquivos
            mp4_files = list(video_dir.glob("*.mp4"))
            metadata_files = list(video_dir.glob("*metadata*"))
            
            print(f"      • Vídeos: {len(mp4_files)}")
            print(f"      • Metadados: {len(metadata_files)}")
            
            # Lista alguns arquivos
            for mp4_file in mp4_files[:3]:  # Mostra apenas os 3 primeiros
                print(f"      - {mp4_file.name}")
            
            if len(mp4_files) > 3:
                print(f"      ... e mais {len(mp4_files) - 3} arquivos")
    else:
        print("   ℹ️ Nenhum vídeo processado encontrado")

def show_speed_config():
    """Mostra configuração de velocidade"""
    cfg = load_cfg()
    content_speed = cfg.get("content_speed", 1.25)
    preserve_pitch = cfg.get("preserve_pitch", True)
    video_duration = cfg.get("video_duration", 61)
    
    print("\n⚡ CONFIGURAÇÃO DE VELOCIDADE:")
    print("=" * 35)
    print(f"📊 Velocidade configurada: {content_speed}x")
    
    if content_speed == 1.0:
        print("ℹ️  Velocidade normal (sem aceleração)")
    elif content_speed > 1.0:
        print(f"⚡ Conteúdo será {content_speed}x mais rápido")
        print(f"   • Duração reduzida em {(1 - 1/content_speed)*100:.1f}%")
    else:
        print(f"🐌 Conteúdo será {content_speed}x mais lento")
        print(f"   • Duração aumentada em {(1/content_speed - 1)*100:.1f}%")
    
    # Mostra configuração de pitch
    print(f"\n🎵 Preservação de pitch: {'✅ Ativada' if preserve_pitch else '❌ Desativada'}")
    if preserve_pitch and content_speed > 2.0:
        print("   ⚠️  Velocidade > 2x: pitch será alterado automaticamente")
    elif preserve_pitch:
        print("   ✅ Tom da voz será mantido original")
    else:
        print("   🎤 Tom da voz será alterado com a velocidade")
    
    # Mostra configuração de duração
    original_duration_needed = video_duration * content_speed
    print(f"\n⏱️ Duração final desejada: {video_duration}s")
    print(f"   • Duração original necessária: {original_duration_needed:.1f}s")
    print(f"   • Cálculo: {video_duration}s × {content_speed}x = {original_duration_needed:.1f}s")
    
    print("\n💡 Para alterar: edite 'content_speed', 'preserve_pitch' e 'video_duration' no config.json")
    print("   • 1.0 = velocidade normal")
    print("   • 1.25 = 25% mais rápido (padrão)")
    print("   • 1.5 = 50% mais rápido")

def show_next_steps():
    """Mostra próximos passos baseado no status"""
    print("\n🎯 PRÓXIMOS PASSOS:")
    print("=" * 30)
    
    cfg = load_cfg()
    processing_checkpoint = load_checkpoint(cfg["paths"]["clips"])
    upload_checkpoint = load_upload_checkpoint(cfg["paths"]["clips"])
    
    if processing_checkpoint:
        print("1. 🔄 Continuar processamento:")
        print("   python main.py <URL_DO_EPISÓDIO>")
        print("   (Use a mesma URL do checkpoint)")
        
    elif upload_checkpoint:
        print("1. 📤 Fazer upload dos cortes:")
        print("   python upload_clips.py")
        print("   (Respeita delays configurados)")
        
    else:
        print("1. 🎬 Iniciar novo processamento:")
        print("   python main.py <URL_DO_EPISÓDIO>")
        print("   (Gera cortes e salva checkpoint)")
    
    print("\n2. 🔧 Outros comandos úteis:")
    print("   python list_clips.py          # Lista todos os vídeos")
    print("   python check_status.py        # Este comando")
    print("   python generate_outros.py     # Gerar outros")

def main():
    """Função principal"""
    check_processing_status()
    show_speed_config()
    show_next_steps()
    
    print("\n" + "=" * 50)
    print("✅ Verificação concluída!")

if __name__ == "__main__":
    main() 