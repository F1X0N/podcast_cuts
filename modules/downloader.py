import yt_dlp
from pathlib import Path
from typing import Dict, Any

def extract_video_info(url: str) -> Dict[str, Any]:
    """
    Extrai informações do vídeo sem fazer download
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "id": info.get("id"),
            "title": info.get("title"),
            "channel": info.get("uploader"),
            "channel_url": info.get("uploader_url"),
            "description": info.get("description", ""),
            "duration": info.get("duration"),
            "view_count": info.get("view_count"),
            "upload_date": info.get("upload_date"),
            "tags": info.get("tags", []),
            "categories": info.get("categories", [])
        }

def download(url: str, out_dir: str = "raw") -> tuple[Path, Dict[str, Any]]:
    """
    Faz o download de vídeo/áudio do episódio e devolve o caminho do .mp4 e metadados
    """
    out_path = Path(out_dir)
    out_path.mkdir(exist_ok=True)
    
    # Primeiro extrai as informações
    video_info = extract_video_info(url)
    
    ydl_opts = {
        "outtmpl": f"{out_dir}/%(id)s.%(ext)s",
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4"
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
    
    video_path = out_path / f"{info['id']}.mp4"
    return video_path, video_info
