# highlighter.py
import openai, textwrap, json
from dotenv import load_dotenv
import os, openai

def find_highlights(transcript, n=3):
    load_dotenv()
    openai.api_key = os.environ["OPENAI_API_KEY"]

    joined = "\n".join(f"[{i}] {seg['text']}" for i, seg in enumerate(transcript))
    prompt = textwrap.dedent(f"""
        Você é editor. Escolha as {n} passagens mais virais para Shorts,
        devolva uma lista JSON com objeto:
        {{ "idx": <nº do segmento>, "hook": "<Título chamativo>" }}
        Transcrição numerada:
        {joined}
    """)
    resp = openai.ChatCompletion.create(model="gpt-4o-mini",
                                        messages=[{"role":"user","content":prompt}],
                                        temperature=0.3)
    return json.loads(resp.choices[0].message.content)
