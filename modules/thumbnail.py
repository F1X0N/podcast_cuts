# thumbnail.py
import openai, base64, requests

def gen_thumbnail(title:str, out="thumb.jpg"):
    prompt = f"minimalista, fundo vibrante, texto grande: {title[:10]}..., foto em 9:16"
    img = openai.Image.create(prompt=prompt, n=1, size="1080x1920")
    img_data = requests.get(img.data[0].url).content
    with open(out, "wb") as f: f.write(img_data)
    return out