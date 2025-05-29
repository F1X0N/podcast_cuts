# youtube_uploader.py
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

GOOGLE_SECRET = os.getenv("GOOGLE_CLIENT_SECRET_JSON", "client_secret.json")
yt = youtube_service(GOOGLE_SECRET)


def youtube_service(secret_json):
    flow = InstalledAppFlow.from_client_secrets_file(secret_json,
            scopes=["https://www.googleapis.com/auth/youtube.upload"])
    creds = flow.run_local_server(port=0)
    return build("youtube","v3",credentials=creds)

def upload(path, title, description, is_short=True):
    yt = youtube_service("client_secret.json")
    body = {
        "snippet":{
            "title": title,
            "description": description,
            "tags":["podcast","cortes","humor"]
        },
        "status":{"privacyStatus":"public"}
    }
    media = MediaFileUpload(path, chunksize=-1, resumable=True, mimetype="video/*")
    yt.videos().insert(part="snippet,status", body=body,
                       media_body=media).execute()
