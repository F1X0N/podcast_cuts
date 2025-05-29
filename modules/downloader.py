import yt_dlp
from pathlib import Path

def download(url: str, out_dir: str = "raw") -> Path:
    """
    Faz o download de vídeo/áudio do episódio e devolve o caminho do .mp4
    """
    out_path = Path(out_dir)
    out_path.mkdir(exist_ok=True)
    ydl_opts = {
        "outtmpl": f"{out_dir}/%(id)s.%(ext)s",
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4"
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
    return out_path / f"{info['id']}.mp4"
