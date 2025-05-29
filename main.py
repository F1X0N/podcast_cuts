# downloader.py
import yt_dlp, pathlib, datetime as dt

def download(url:str, out_dir="raw") -> pathlib.Path:
    path = pathlib.Path(out_dir); path.mkdir(exist_ok=True)
    ydl_opts = {"outtmpl": f"{out_dir}/%(id)s.%(ext)s", "format": "bestvideo+bestaudio/best"}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
    return path / f"{info['id']}.mp4"
