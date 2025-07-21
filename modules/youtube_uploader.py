import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError
from pathlib import Path
import json

# Escopos mais específicos para reduzir problemas de verificação
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]
TOKEN_CACHE = "token.json"

def load_cached_token():
    """Carrega o token salvo do cache"""
    if os.path.exists(TOKEN_CACHE):
        try:
            with open(TOKEN_CACHE, 'r') as f:
                token_data = json.load(f)
            return Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception as e:
            print(f"⚠️  Erro ao carregar token cache: {e}")
            return None
    return None

def save_token_to_cache(creds):
    """Salva o token no cache para uso futuro"""
    try:
        token_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        with open(TOKEN_CACHE, 'w') as f:
            json.dump(token_data, f)
        print("✅ Token salvo no cache para uso futuro")
    except Exception as e:
        print(f"⚠️  Erro ao salvar token: {e}")

def youtube_service(secret_json="client_secret.json"):
    """Inicializa o serviço do YouTube com autenticação OAuth2 e cache de token"""
    try:
        # Tenta carregar token do cache
        creds = load_cached_token()
        
        if creds and creds.valid:
            print("✅ Usando token salvo do cache")
            return build("youtube", "v3", credentials=creds)
        
        # Se o token expirou, tenta renovar
        if creds and creds.expired and creds.refresh_token:
            try:
                print("🔄 Renovando token expirado...")
                creds.refresh(Request())
                save_token_to_cache(creds)
                return build("youtube", "v3", credentials=creds)
            except RefreshError:
                print("⚠️  Token expirado e não foi possível renovar")
                # Remove token inválido
                if os.path.exists(TOKEN_CACHE):
                    os.remove(TOKEN_CACHE)
        
        # Se não há token válido, faz nova autenticação
        print("🔐 Fazendo nova autenticação...")
        flow = InstalledAppFlow.from_client_secrets_file(
            secret_json, 
            scopes=SCOPES
        )
        
        # Configurações para desenvolvimento local
        creds = flow.run_local_server(
            port=0,
            access_type='offline',
            prompt='consent'
        )
        
        # Salva o token no cache
        save_token_to_cache(creds)
        
        return build("youtube", "v3", credentials=creds)
        
    except Exception as e:
        print(f"Erro na autenticação: {e}")
        print("\nSoluções possíveis:")
        print("1. Verifique se você adicionou seu email como usuário de teste no Google Cloud Console")
        print("2. Acesse: https://console.cloud.google.com/apis/credentials")
        print("3. Vá para 'OAuth consent screen' > 'Test users' > 'Add Users'")
        print("4. Adicione o email da conta que você está usando")
        raise

def upload(
        video_path: str, 
        title: str, 
        description: str, 
        tags=None,
        secret_json="client_secret.json"
    ):
    """Faz upload de um vídeo para o YouTube"""
    
    tags = tags or ["podcast", "cortes", "clipverso"]
    
    try:
        yt = youtube_service(secret_json)
        
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags
            },
            "status": {"privacyStatus": "public"}
        }
        
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = yt.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
            fields="id"
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Upload progresso: {int(status.progress() * 100)}%")
        
        video_id = response.get("id")
        print(f"Upload concluído! ID do vídeo: {video_id}")
        return video_id
        
    except Exception as e:
        print(f"Erro no upload: {e}")
        raise

def clear_token_cache():
    """Remove o token cache para forçar nova autenticação"""
    if os.path.exists(TOKEN_CACHE):
        os.remove(TOKEN_CACHE)
        print("✅ Cache de token removido")
    else:
        print("ℹ️  Nenhum cache de token encontrado")