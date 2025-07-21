#!/usr/bin/env python3
"""
Script para gerenciar o cache de token do YouTube
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.youtube_uploader import youtube_service, clear_token_cache, load_cached_token
from google.oauth2.credentials import Credentials

def check_token_status():
    """Verifica o status do token cache"""
    print("🔍 Verificando status do token...")
    print("=" * 50)
    
    creds = load_cached_token()
    
    if creds:
        print("✅ Token encontrado no cache")
        print(f"📅 Válido: {creds.valid}")
        print(f"📅 Expirado: {creds.expired}")
        print(f"🔄 Tem refresh token: {creds.refresh_token is not None}")
        
        if creds.valid:
            print("🎉 Token está válido e pronto para uso!")
            return True
        elif creds.expired and creds.refresh_token:
            print("⚠️  Token expirado, mas pode ser renovado")
            return True
        else:
            print("❌ Token inválido ou expirado")
            return False
    else:
        print("❌ Nenhum token encontrado no cache")
        return False

def test_authentication():
    """Testa a autenticação com o YouTube"""
    print("\n🧪 Testando autenticação...")
    print("=" * 30)
    
    try:
        yt = youtube_service()
        print("✅ Autenticação bem-sucedida!")
        
        # Testa uma chamada simples
        response = yt.channels().list(
            part='snippet',
            mine=True
        ).execute()
        
        if response['items']:
            channel = response['items'][0]
            print(f"📺 Canal: {channel['snippet']['title']}")
            print(f"🆔 ID: {channel['id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na autenticação: {e}")
        return False

def main():
    """Função principal"""
    if len(sys.argv) < 2:
        print("Uso: python manage_token.py [comando]")
        print("\nComandos disponíveis:")
        print("  status     - Verifica o status do token")
        print("  test       - Testa a autenticação")
        print("  clear      - Remove o token cache")
        print("  auth       - Força nova autenticação")
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        check_token_status()
        
    elif command == "test":
        if check_token_status():
            test_authentication()
        else:
            print("\n💡 Execute 'python manage_token.py auth' para fazer nova autenticação")
            
    elif command == "clear":
        clear_token_cache()
        
    elif command == "auth":
        print("🔐 Forçando nova autenticação...")
        clear_token_cache()
        test_authentication()
        
    else:
        print(f"❌ Comando '{command}' não reconhecido")

if __name__ == "__main__":
    main() 