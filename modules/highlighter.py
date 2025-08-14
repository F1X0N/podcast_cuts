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

Escolha os {n} segmentos mais virais/de impacto com o objetivo de criar um vídeo viral e que possa gerar engajamento, com o objetivo de gerar mais visualizações, curtidas e comentários.

INSTRUÇÕES:
1. Considere o título e canal do vídeo original para criar títulos contextuais e chamativos;
2. Use tags que combinem com o tema do vídeo original + viralidade;
3. Títulos devem ser chamativos e relacionados ao conteúdo do trecho;
4. Tags devem incluir palavras-chave do tema + termos virais;
    - Importante: Tags não devem conter hashtags.
5. Crie uma breve descrição do trecho selecionado para ser usada no vídeo.
6. O trecho, além de viral, deve ser relevante no vídeo original e ter a intenção de gerar o CTA (Call to Action) para o usuário comentar, curtir, compartilhar, etc.
7. Para cada highlight, além do título, tags e descrição, crie uma pergunta curta e chamativa que seja relevante para o trecho e que possa gerar engajamento.

Responda APENAS com JSON: [{{"idx": <int>, "hook": "<título chamativo e contextual>", "tags": ["<tag1>", "<tag2>", ...], "description": "<descrição do trecho selecionado>", "question": "<pergunta curta e chamativa>"}}]

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
        parsed = json.loads(content)
        
        # Garante que sempre retorne uma lista
        if isinstance(parsed, dict):
            # Se retornou um objeto único, converte para lista
            parsed = [parsed]
        elif isinstance(parsed, list):
            # Se já é uma lista, mantém como está
            pass
        else:
            # Se não é nem dict nem list, erro
            raise ValueError(f"Formato inesperado: {type(parsed)}")
        
        return parsed
    except Exception as e:
        save_error_log(f"Resposta bruta da LLM:\n{content}\nErro: {e}", None)
        raise RuntimeError(f"Erro ao decodificar JSON da LLM. Veja logs/erros.log para detalhes.")