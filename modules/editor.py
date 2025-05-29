# editor.py
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import srt, datetime as dt

def make_clip(video_path, highlight, transcript, out_dir="clips"):
    out = pathlib.Path(out_dir); out.mkdir(exist_ok=True)
    seg = transcript[highlight["idx"]]
    clip = (VideoFileClip(video_path)
            .subclip(seg["start"], seg["end"])
            .fx( vfx.resize, width=1080 )   # formato vertical 1080 × 1920
            .fx( vfx.crop, x_center=0.5, y_center=0.4, width=1080, height=1920 ))
    
    # Legenda “burned in”
    caption = TextClip(seg["text"], font="Arial-Bold",
                       fontsize=60, method='caption', align='South',
                       size=(1000, None))
    caption = caption.set_position(("center","bottom")).set_duration(clip.duration)
    final = CompositeVideoClip([clip, caption])
    outfile = out/f"{highlight['hook']}.mp4"
    final.write_videofile(outfile, codec="libx264", fps=30)
    return outfile
