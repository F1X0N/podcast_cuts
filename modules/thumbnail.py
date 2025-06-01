import os, requests
from dotenv import load_dotenv
from modules.llm_utils import call_llm

load_dotenv()

def gen_thumbnail(title: str, out_path="thumb.png"):
    prompt = (f"Minimalista, gradiente azul-roxo, texto grande '{title[:12]}', "
              "ícones de microfone e tesoura, 1080x1920, estilo flat clean.")
    response = call_llm(
        role="thumbnail",
        prompt=prompt,
        image=True,
        n=1,
        size="1024x1024",
        quality="standard"
    )
    img_data = requests.get(response.data[0].url).content
    with open(out_path, "wb") as f:
        f.write(img_data)
    return out_path
