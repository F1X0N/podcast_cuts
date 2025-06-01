# modules/editor.py
from pathlib import Path
import moviepy.editor as mp
from PIL import Image, ImageEnhance
import re
import unicodedata

def sanitize_filename(name, max_length=50):
    # Remove acentos
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    # Remove caracteres especiais
    name = re.sub(r'[^a-zA-Z0-9_\- ]', '', name)
    # Substitui espaços por underline
    name = name.replace(' ', '_')
    # Limita o tamanho
    return name[:max_length]

def make_clip(video_path: str, highlight: dict, transcript: list,
              out_dir: str = "clips") -> Path:
    """
    Recorta, converte para vertical 9:16, "queima" legenda e devolve o caminho final.
    Garante que o clipe tenha no mínimo 1 minuto de duração.
    """
    seg = transcript[highlight["idx"]]
    Path(out_dir).mkdir(exist_ok=True)

    # Carrega o vídeo
    clip = mp.VideoFileClip(video_path)
    video_duration = clip.duration

    # Define início e fim do corte
    start = seg["start"]
    end = seg["end"]
    min_duration = 60  # 1 minuto
    if end - start < min_duration:
        end = min(start + min_duration, video_duration)

    # Recorta o trecho
    clip = clip.subclip(start, end)
    
    # Redimensiona para 1080p mantendo proporção
    clip = clip.resize(width=1080)
    
    # Calcula as dimensões para o crop vertical
    w, h = clip.size
    x_center = w/2
    y_center = h/2
    width = 1080
    height = 1920

    # Garante que width e height sejam pares
    width = int(width) // 2 * 2
    height = int(height) // 2 * 2
    
    # Faz o crop vertical
    clip = clip.crop(x_center=x_center, y_center=y_center,
                    width=width, height=height)

    # Garante que o vídeo final tenha largura e altura pares
    final_w, final_h = clip.size
    if final_w % 2 != 0 or final_h % 2 != 0:
        new_w = final_w // 2 * 2
        new_h = final_h // 2 * 2
        clip = clip.resize(newsize=(new_w, new_h))

    # Adiciona a legenda
    caption = (mp.TextClip(seg["text"], fontsize=60, font="Arial-Bold", color="white",
                        method="caption", size=(1000, None))
               .set_position(("center", "bottom"))
               .set_duration(clip.duration)
               )
    
    # Combina o vídeo com a legenda
    final = mp.CompositeVideoClip([clip, caption])
    
    # Salva o arquivo com nome seguro
    safe_hook = sanitize_filename(highlight['hook'])
    outfile = Path(out_dir) / f"{safe_hook}.mp4"
    final.write_videofile(str(outfile), codec="libx264", fps=30, preset="ultrafast",
                         ffmpeg_params=["-profile:v", "main", "-pix_fmt", "yuv420p"],
                         audio_codec="aac")
    
    return outfile