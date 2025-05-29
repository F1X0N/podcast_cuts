import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_CACHE = "token.json"

def youtube_service(secret_json="client_secret.json"):
    flow = InstalledAppFlow.from_client_secrets_file(secret_json, scopes=SCOPES)
    creds = flow.run_local_server(port=0)
    return build("youtube", "v3", credentials=creds)

def upload(video_path: str, title: str, description: str, tags=None,
           secret_json="client_secret.json"):
    tags = tags or ["podcast", "cortes", "clipverso"]
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
    request = yt.videos().insert(part="snippet,status",
                                 body=body,
                                 media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
    return response.get("id")