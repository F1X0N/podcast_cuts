# modules/highlighter.py
import os, json, textwrap
from dotenv import load_dotenv
from modules.llm_utils import call_llm, save_error_log
load_dotenv()

SYSTEM_MSG = (
    "Você é um editor de cortes especializado em criar conteúdo viral para Shorts. "
    "Receberá a transcrição numerada de um episódio e deve escolher os melhores trechos virais, "
    "criando títulos chamativos e tags relevantes baseados no contexto do vídeo original."
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

def find_highlights(transcript: list, video_info: dict = None, n: int = 3):
    joined = "\n".join(f"[{i}] {seg['text']}" for i, seg in enumerate(transcript))
    
    # Contexto do vídeo original
    context_info = ""
    if video_info:
        context_info = f"""
        CONTEXTO DO VÍDEO ORIGINAL:
        - Título: {video_info.get('title', 'N/A')}
        - Canal: {video_info.get('channel', 'N/A')}
        - Duração: {video_info.get('duration', 0) // 60}min
        - Tags originais: {', '.join(video_info.get('tags', [])[:5])}
        """
    
    prompt = textwrap.dedent(f"""
        {context_info}
        
        Escolha os {n} segmentos mais virais/de impacto.
        
        INSTRUÇÕES:
        1. Considere o título e canal do vídeo original para criar títulos contextuais
        2. Use tags que combinem com o tema do vídeo original + viralidade
        3. Títulos devem ser chamativos e relacionados ao conteúdo do trecho
        4. Tags devem incluir palavras-chave do tema + termos virais
        
        Responda APENAS com JSON: [{{"idx": <int>, "hook": "<título chamativo e contextual>", "tags": ["<tag1>", "<tag2>", ...]}}]
        
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