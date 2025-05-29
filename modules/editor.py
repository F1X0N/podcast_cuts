# modules/editor.py
from pathlib import Path
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, vfx

def make_clip(video_path: str, highlight: dict, transcript: list,
              out_dir: str = "clips") -> Path:
    """
    Recorta, converte para vertical 9:16, “queima” legenda e devolve o caminho final.
    """
    seg = transcript[highlight["idx"]]
    Path(out_dir).mkdir(exist_ok=True)

    clip = (VideoFileClip(video_path)
            .subclip(seg["start"], seg["end"])
            .fx(vfx.resize, width=1080)          # garante largura 1080
            .fx(vfx.crop, x_center=clip.w/2, y_center=clip.h/2,
                width=1080, height=1920)         # crop vertical
            )

    caption = (TextClip(seg["text"], fontsize=60, font="Arial-Bold", color="white",
                        method="caption", size=(1000, None))
               .set_position(("center", "bottom"))
               .set_duration(clip.duration)
               )
    final = CompositeVideoClip([clip, caption])
    outfile = Path(out_dir) / f"{highlight['hook']}.mp4"
    final.write_videofile(outfile, codec="libx264", fps=30, preset="ultrafast")
    return outfile