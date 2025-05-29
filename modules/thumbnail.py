import os, requests, openai
from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def gen_thumbnail(title: str, out_path="thumb.png"):
    prompt = (f"Minimalista, gradiente azul-roxo, texto grande '{title[:12]}', "
              "ícones de microfone e tesoura, 1080x1920, estilo flat clean.")
    img = openai.Image.create(prompt=prompt, n=1, size="1080x1920")
    img_data = requests.get(img.data[0].url).content
    with open(out_path, "wb") as f:
        f.write(img_data)
    return out_path
