# modules/highlighter.py
import os, json, textwrap
from dotenv import load_dotenv
from modules.llm_utils import call_llm, save_error_log
load_dotenv()

SYSTEM_MSG = (
    "Você é um editor de cortes. Receberá a transcrição numerada de um episódio "
    "e deve escolher os melhores trechos virais para Shorts, devolvendo JSON."
)

def clean_json_response(content):
    # Remove blocos de código markdown (```json ... ```)
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()

def find_highlights(transcript: list, n: int = 3):
    joined = "\n".join(f"[{i}] {seg['text']}" for i, seg in enumerate(transcript))
    prompt = textwrap.dedent(f"""
        Escolha os {n} segmentos mais virais/de impacto.
        Responda APENAS com JSON: [{{"idx": <int>, "hook": "<título chamativo>"}}]
        Transcrição:
        {joined}
    """)
    response = call_llm(
        role="highlighter",
        messages=[
            {"role": "system", "content": SYSTEM_MSG},
            {"role": "user", "content": prompt}
        ]
    )
    content = getattr(response.choices[0].message, "content", "").strip()
    if not content:
        save_error_log("Resposta vazia da LLM na etapa highlighter.", None)
        raise RuntimeError("A LLM retornou uma resposta vazia na etapa de seleção de cortes.")
    content = clean_json_response(content)
    try:
        return json.loads(content)
    except Exception as e:
        save_error_log(f"Resposta bruta da LLM:\n{content}\nErro: {e}", None)
        raise RuntimeError(f"Erro ao decodificar JSON da LLM. Veja logs/erros.log para detalhes.")