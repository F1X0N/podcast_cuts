# modules/editor.py
from pathlib import Path
import moviepy.editor as mp
from PIL import Image, ImageEnhance
import re
import unicodedata
import os

def sanitize_filename(name, max_length=50):
    # Remove acentos
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    # Remove caracteres especiais
    name = re.sub(r'[^a-zA-Z0-9_\- ]', '', name)
    # Substitui espaços por underline
    name = name.replace(' ', '_')
    # Limita o tamanho
    return name[:max_length]

def get_font_path():
    # Usa Roboto-Bold.ttf da pasta fonts/ se existir, senão Arial
    font_dir = os.path.join(os.getcwd(), "fonts")
    font_path = os.path.join(font_dir, "Roboto-Bold.ttf")
    if os.path.exists(font_path):
        print(f"Usando fonte: {font_path}")
        return font_path
    print("Usando fonte fallback: Arial")
    return "Arial"

def make_clip(video_path: str, highlight: dict, transcript: list,
              out_dir: str = "clips") -> Path:
    """
    Recorta, converte para vertical 9:16, gera legendas dinâmicas estilizadas e devolve o caminho final.
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
    
    # Redimensiona para 1080x1920 (vertical)
    clip = clip.resize(width=1080)
    w, h = clip.size
    x_center = w/2
    y_center = h/2
    width = 1080
    height = 1920
    width = int(width) // 2 * 2
    height = int(height) // 2 * 2
    clip = clip.crop(x_center=x_center, y_center=y_center, width=width, height=height)
    final_w, final_h = clip.size
    if final_w % 2 != 0 or final_h % 2 != 0:
        new_w = final_w // 2 * 2
        new_h = final_h // 2 * 2
        clip = clip.resize(newsize=(new_w, new_h))

    # Gera legendas dinâmicas sincronizadas
    font_path = get_font_path()
    fontsize = int(0.06 * height)  # 6% da altura
    margin_bottom = int(0.04 * height)  # 4% da altura
    legendas = []
    faixa = None
    for segm in transcript:
        # Só inclui legendas dentro do corte
        if segm["end"] <= start or segm["start"] >= end:
            continue
        seg_start = max(segm["start"], start) - start
        seg_end = min(segm["end"], end) - start
        txt = segm["text"]
        # Faixa preta translúcida
        if faixa is None:
            faixa = mp.ColorClip(size=(width, fontsize+40), color=(0,0,0)).set_opacity(0.5)
            faixa = faixa.set_position(("center", height - fontsize - margin_bottom - 20)).set_duration(clip.duration)
        # Legenda estilizada
        try:
            legenda = mp.TextClip(txt, fontsize=fontsize, font=font_path, color="white",
                                  stroke_color="black", stroke_width=2, method="caption", size=(width-80, None)) \
                .set_start(seg_start).set_end(seg_end) \
                .set_position(("center", height - fontsize - margin_bottom))
            print(f"Legenda criada: {txt}")
        except Exception as e:
            print(f"Erro ao criar legenda: {txt} | Erro: {e}")
            continue
        legendas.append(legenda)
    # Combina vídeo, faixa e legendas
    elementos = [clip]
    if faixa: elementos.append(faixa)
    elementos += legendas
    final = mp.CompositeVideoClip(elementos)
    
    # Salva o arquivo com nome seguro
    safe_hook = sanitize_filename(highlight['hook'])
    outfile = Path(out_dir) / f"{safe_hook}.mp4"
    final.write_videofile(str(outfile), codec="libx264", fps=30, preset="ultrafast",
                         ffmpeg_params=["-profile:v", "main", "-pix_fmt", "yuv420p"],
                         audio_codec="aac")
    
    return outfile