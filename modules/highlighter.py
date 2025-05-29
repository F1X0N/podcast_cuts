# modules/highlighter.py
import os, json, textwrap, openai
from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

SYSTEM_MSG = (
    "Você é um editor de cortes. Receberá a transcrição numerada de um episódio "
    "e deve escolher os melhores trechos virais para Shorts, devolvendo JSON."
)

def find_highlights(transcript: list, n: int = 3):
    joined = "\n".join(f"[{i}] {seg['text']}" for i, seg in enumerate(transcript))
    prompt = textwrap.dedent(f"""
        Escolha os {n} segmentos mais virais/de impacto.
        Responda APENAS com JSON: [{{"idx": <int>, "hook": "<título chamativo>"}}]
        Transcrição:
        {joined}
    """)
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role":"system", "content": SYSTEM_MSG},
                  {"role":"user", "content": prompt}],
        temperature=0.4,
    )
    return json.loads(resp.choices[0].message.content)