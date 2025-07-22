#!/usr/bin/env python3
"""
Script para atualizar os outros com versões melhoradas
"""

import os
import shutil
from pathlib import Path

def backup_old_outros():
    """Faz backup dos outros antigos"""
    assets_dir = Path("assets/outros")
    backup_dir = Path("assets/outros_backup")
    
    if not assets_dir.exists():
        print("❌ Diretório de outros não encontrado")
        return False
    
    # Cria diretório de backup
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Move outros antigos para backup
    for i in range(1, 4):
        old_file = assets_dir / f"outro{i}.mp4"
        if old_file.exists():
            backup_file = backup_dir / f"outro{i}_old.mp4"
            shutil.move(str(old_file), str(backup_file))
            print(f"📦 Backup criado: {backup_file}")
    
    return True

def update_outros():
    """Atualiza os outros com versões melhoradas"""
    print("🔄 Atualizando outros do ClipVerso...")
    
    # Faz backup dos antigos
    if not backup_old_outros():
        return False
    
    # Gera novos outros melhorados
    print("\n🎬 Gerando outros melhorados...")
    os.system("poetry run python generate_outros_enhanced.py")
    
    print("\n✅ Outros atualizados com sucesso!")
    print("📁 Backup dos antigos salvo em: assets/outros_backup/")
    
    return True

def main():
    """Função principal"""
    print("=" * 50)
    print("ATUALIZADOR DE OUTROS - CLIPVERSO")
    print("=" * 50)
    
    if update_outros():
        print("\n🎉 Atualização concluída!")
        print("   Os novos outros têm:")
        print("   ✅ Animações criativas e fluidas")
        print("   ✅ Efeitos visuais bonitos")
        print("   ✅ Logo integrado")
        print("   ✅ Sincronização perfeita com TTS")
        print("   ✅ Textos bem posicionados")
    else:
        print("\n❌ Erro na atualização")

if __name__ == "__main__":
    main() 