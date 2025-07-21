# modules/editor.py
from pathlib import Path
import moviepy.editor as mp
from PIL import Image, ImageEnhance
import re
import unicodedata
import os
import json
import numpy as np

def sanitize_filename(name, max_length=50):
    # Remove acentos
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    # Remove caracteres especiais
    name = re.sub(r'[^a-zA-Z0-9_\- ]', '', name)
    # Substitui espaços por underline
    name = name.replace(' ', '_')
    # Limita o tamanho
    return name[:max_length]

def get_font_path():
    # Usa Roboto-Bold.ttf da pasta fonts/ se existir, senão Arial
    font_dir = os.path.join(os.getcwd(), "fonts")
    font_path = os.path.join(font_dir, "Roboto-Bold.ttf")
    if os.path.exists(font_path):
        print(f"Usando fonte: {font_path}")
        return font_path
    print("Usando fonte fallback: Arial")
    return "Arial"

def get_checkpoint_path(out_dir: str) -> Path:
    """Retorna o caminho do arquivo de checkpoint"""
    return Path(out_dir) / "checkpoint.json"

def save_checkpoint(out_dir: str, video_path: str, highlight: dict, transcript: list, video_info: dict = None):
    """Salva o estado atual do processamento"""
    checkpoint = {
        "video_path": video_path,
        "highlight": highlight,
        "transcript": transcript,
        "video_info": video_info or {}
    }
    checkpoint_path = get_checkpoint_path(out_dir)
    # Cria o diretório se não existir
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checkpoint_path, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)
    print(f"Checkpoint salvo em: {checkpoint_path}")

def load_checkpoint(out_dir: str) -> dict:
    """Carrega o último checkpoint salvo"""
    checkpoint_path = get_checkpoint_path(out_dir)
    if not checkpoint_path.exists():
        return None
    with open(checkpoint_path, "r", encoding="utf-8") as f:
        return json.load(f)

def clear_checkpoint(out_dir: str):
    """Remove o arquivo de checkpoint"""
    checkpoint_path = get_checkpoint_path(out_dir)
    if checkpoint_path.exists():
        checkpoint_path.unlink()
        print("Checkpoint removido")

def segment_text(text: str, max_chars: int = 20) -> list:
    """
    Segmenta o texto em partes menores, garantindo uma linha por legenda.
    """
    # Pontuações que indicam pausa natural
    pausas = ['.', '!', '?', ':', ';', ',', '...']
    
    # Se o texto já é curto, retorna como está
    if len(text) <= max_chars:
        return [text]
    
    segmentos = []
    palavras = text.split()
    segmento_atual = []
    chars_atual = 0
    
    for palavra in palavras:
        # Verifica se adicionar esta palavra ultrapassaria o limite
        if chars_atual + len(palavra) + 1 > max_chars:
            # Se o segmento atual termina com pontuação, é um bom lugar para quebrar
            if segmento_atual and any(segmento_atual[-1].endswith(p) for p in pausas):
                segmentos.append(' '.join(segmento_atual))
                segmento_atual = [palavra]
                chars_atual = len(palavra)
            else:
                # Procura a última pontuação no segmento atual
                ultima_pausa = -1
                for i, p in enumerate(segmento_atual):
                    if any(p.endswith(pausa) for pausa in pausas):
                        ultima_pausa = i
                
                if ultima_pausa >= 0:
                    # Quebra no último ponto de pausa
                    segmentos.append(' '.join(segmento_atual[:ultima_pausa + 1]))
                    segmento_atual = segmento_atual[ultima_pausa + 1:] + [palavra]
                    chars_atual = sum(len(p) for p in segmento_atual) + len(segmento_atual) - 1
                else:
                    # Se não encontrou pausa, força a quebra
                    segmentos.append(' '.join(segmento_atual))
                    segmento_atual = [palavra]
                    chars_atual = len(palavra)
        else:
            segmento_atual.append(palavra)
            chars_atual += len(palavra) + 1
    
    if segmento_atual:
        segmentos.append(' '.join(segmento_atual))
    
    return segmentos

def create_animated_text(text: str, duration: float, font_path: str, fontsize: int, width: int, 
                        position: tuple) -> mp.TextClip:
    """
    Cria um TextClip com animações básicas.
    """
    # Cria o clip base com o texto
    clip = mp.TextClip(text,
        fontsize=fontsize,
        font=font_path,
        color="white",
        stroke_color="black",
        stroke_width=2,
        method="caption",
        size=(width-80, None))
    
    # Define a duração total
    clip = clip.set_duration(duration)
    
    # Adiciona um pequeno fade in/out
    clip = clip.crossfadein(0.1).crossfadeout(0.1)
    
    # Posiciona o clip
    return clip.set_position(position)

def create_typing_effect(text: str, duration: float, font_path: str, fontsize: int, width: int,
                        position: tuple, typing_speed: float = 0.03) -> mp.TextClip:
    """
    Cria um TextClip com efeito de digitação.
    """
    # Calcula quantos caracteres devem aparecer por frame
    chars_per_second = 1 / typing_speed
    total_chars = len(text)
    
    def make_frame(t):
        # Calcula quantos caracteres devem estar visíveis
        visible_chars = min(int(t * chars_per_second), total_chars)
        return text[:visible_chars]
    
    # Cria o clip base
    base_clip = mp.TextClip(make_frame,
        fontsize=fontsize,
        font=font_path,
        color="white",
        stroke_color="black",
        stroke_width=2,
        method="caption",
        size=(width-80, None))
    
    # Define a duração total
    base_clip = base_clip.set_duration(duration)
    
    # Posiciona o clip
    return base_clip.set_position(position)

def highlight_keywords(text: str) -> str:
    """
    Destaca palavras importantes no texto usando cores diferentes.
    """
    # Lista de palavras-chave para destacar (pode ser expandida)
    keywords = [
        "importante", "crucial", "essencial", "principal",
        "incrível", "fantástico", "surpreendente", "extraordinário",
        "nunca", "sempre", "jamais", "definitivamente"
    ]
    
    # Cores para destacar (em formato hex)
    colors = ["#FFD700", "#FF69B4", "#00FF00", "#FF4500"]
    
    # Divide o texto em palavras
    words = text.split()
    highlighted_words = []
    
    for word in words:
        # Remove pontuação para comparação
        clean_word = word.strip('.,!?;:')
        if clean_word.lower() in keywords:
            # Escolhe uma cor aleatória
            color = colors[len(highlighted_words) % len(colors)]
            # Adiciona a palavra com a cor
            highlighted_words.append(f'<color={color}>{word}</color>')
        else:
            highlighted_words.append(word)
    
    return ' '.join(highlighted_words)

def create_template_clip(width: int, height: int, duration: float) -> mp.VideoClip:
    """
    Cria um template com header e footer baseado no molde fornecido.
    """
    # Cria um clip de fundo com gradiente azul/roxo
    def make_background_frame(t):
        # Gradiente horizontal azul para roxo
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        for x in range(width):
            # Gradiente de azul (esquerda) para roxo (direita)
            blue_ratio = 1 - (x / width)
            purple_ratio = x / width
            
            # Cores base (azul escuro e roxo escuro)
            blue_color = np.array([30, 30, 100])  # Azul escuro
            purple_color = np.array([80, 30, 100])  # Roxo escuro
            
            # Mistura as cores
            color = (blue_color * blue_ratio + purple_color * purple_ratio).astype(np.uint8)
            frame[:, x] = color
        
        return frame
    
    background = mp.VideoClip(make_background_frame, duration=duration)
    
    # Calcula dimensões das seções
    header_height = int(height * 0.15)  # 15% para header
    footer_height = int(height * 0.10)  # 10% para footer
    video_area_height = height - header_height - footer_height
    
    # Cria header
    header_elements = []
    
    # Logo circular "CV"
    logo_size = int(header_height * 0.6)
    logo_x = int(width * 0.05)
    logo_y = header_height // 2
    
    # Cria logo circular com gradiente
    def make_logo_frame(t):
        frame = np.zeros((logo_size, logo_size, 3), dtype=np.uint8)
        center = logo_size // 2
        radius = logo_size // 2 - 5
        
        for y in range(logo_size):
            for x in range(logo_size):
                dist = np.sqrt((x - center)**2 + (y - center)**2)
                if dist <= radius:
                    # Gradiente circular azul para roxo
                    angle = np.arctan2(y - center, x - center)
                    ratio = (angle + np.pi) / (2 * np.pi)
                    blue_ratio = 1 - ratio
                    purple_ratio = ratio
                    
                    blue_color = np.array([100, 150, 255])  # Azul claro
                    purple_color = np.array([200, 100, 255])  # Roxo claro
                    color = (blue_color * blue_ratio + purple_color * purple_ratio).astype(np.uint8)
                    frame[y, x] = color
        return frame
    
    logo_clip = mp.VideoClip(make_logo_frame, duration=duration)
    logo_clip = logo_clip.set_position((logo_x, logo_y - logo_size//2))
    header_elements.append(logo_clip)
    
    # Texto "CV" no logo
    cv_text = mp.TextClip("CV", fontsize=int(logo_size * 0.4), font="Arial-Bold", 
                         color="white", stroke_color="black", stroke_width=1)
    cv_text = cv_text.set_position((logo_x + logo_size//2 - cv_text.w//2, 
                                   logo_y - cv_text.h//2))
    cv_text = cv_text.set_duration(duration)
    header_elements.append(cv_text)
    
    # Título "CLIPVERSO"
    title_x = logo_x + logo_size + int(width * 0.03)
    title_y = header_height // 2 - int(header_height * 0.15)
    
    title_clip = mp.TextClip("CLIPVERSO", fontsize=int(header_height * 0.25), 
                            font="Arial-Bold", color="white")
    title_clip = title_clip.set_position((title_x, title_y))
    title_clip = title_clip.set_duration(duration)
    header_elements.append(title_clip)
    
    # Subtitle "CANAL DE CORTES"
    subtitle_y = title_y + int(header_height * 0.25)
    subtitle_clip = mp.TextClip("CANAL DE CORTES", fontsize=int(header_height * 0.15), 
                               font="Arial", color="#87CEEB")  # Azul claro
    subtitle_clip = subtitle_clip.set_position((title_x, subtitle_y))
    subtitle_clip = subtitle_clip.set_duration(duration)
    header_elements.append(subtitle_clip)
    
    # Linha superior do header
    line_y = header_height - 2
    line_clip = mp.ColorClip(size=(width, 2), color=[100, 150, 255], duration=duration)
    line_clip = line_clip.set_position((0, line_y))
    header_elements.append(line_clip)
    
    # Cria footer
    footer_elements = []
    
    # Linha inferior do footer
    footer_line_y = header_height + video_area_height
    footer_line_clip = mp.ColorClip(size=(width, 2), color=[100, 150, 255], duration=duration)
    footer_line_clip = footer_line_clip.set_position((0, footer_line_y))
    footer_elements.append(footer_line_clip)
    
    # Texto do footer
    footer_text = "Se inscreva • Dé o like • @clipverso-ofc"
    footer_text_y = footer_line_y + int(footer_height * 0.3)
    footer_text_clip = mp.TextClip(footer_text, fontsize=int(footer_height * 0.3), 
                                  font="Arial-Bold", color="white")
    footer_text_clip = footer_text_clip.set_position(("center", footer_text_y))
    footer_text_clip = footer_text_clip.set_duration(duration)
    footer_elements.append(footer_text_clip)
    
    # Combina todos os elementos
    template = mp.CompositeVideoClip([background] + header_elements + footer_elements, 
                                   size=(width, height))
    
    return template

def make_clip(
        video_path: str, 
        highlight: dict, 
        transcript: list,
        out_dir: str = "clips"
    ) -> Path:
    """
    Recorta, converte para vertical 9:16, gera legendas dinâmicas estilizadas e devolve o caminho final.
    Garante que o clipe tenha no mínimo 1 minuto de duração.
    """
    seg = transcript[highlight["idx"]]
    Path(out_dir).mkdir(exist_ok=True)

    clip = mp.VideoFileClip(video_path)
    video_duration = clip.duration

    # Define início e fim do corte
    start = seg["start"]
    end = seg["end"]
    min_duration = 70  # 1 minuto
    if end - start < min_duration:
        end = min(start + min_duration, video_duration)

    # Recorta o trecho
    clip = clip.subclip(start, end)

    # Define dimensões finais do template
    final_width = 1080
    final_height = 1920
    
    # Calcula dimensões das seções do template
    header_height = int(final_height * 0.15)  # 15% para header
    footer_height = int(final_height * 0.10)  # 10% para footer
    video_area_height = final_height - header_height - footer_height
    video_area_width = final_width - 40  # Margem de 20px de cada lado
    
    # Redimensiona o vídeo para caber na área de vídeo do template
    clip = clip.resize(height=video_area_height)
    w, h = clip.size
    
    # Se o vídeo for mais largo que a área disponível, corta as laterais
    if w > video_area_width:
        x_center = w // 2
        y_center = h // 2
        clip = clip.crop(x_center=x_center, y_center=y_center, 
                        width=video_area_width, height=video_area_height)
    else:
        # Se for mais estreito, centraliza
        clip = clip.resize(width=video_area_width, height=video_area_height)
    
    # Garante dimensões pares
    final_w, final_h = clip.size
    if final_w % 2 != 0 or final_h % 2 != 0:
        new_w = final_w // 2 * 2
        new_h = final_h // 2 * 2
        clip = clip.resize(newsize=(new_w, new_h))
    
    print(f"Tamanho do vídeo na área: {final_w}x{final_h}")

    font_path = get_font_path()
    fontsize = int(0.06 * video_area_height)  # 4% da altura da área de vídeo
    margin_bottom = int(0.08 * video_area_height)  # Margem dentro da área de vídeo
    legendas = []
    
    # Testa se a fonte está funcionando
    try:
        test_clip = mp.TextClip("Teste", fontsize=fontsize, font=font_path, fontweight="bold", color="white")
        test_clip.close()
    except Exception as e:
        font_path = "Arial"
    
    print(f"Processando {len(transcript)} segmentos de texto...")
    for i, segm in enumerate(transcript):
        # Só inclui legendas dentro do corte
        if segm["end"] <= start or segm["start"] >= end:
            print(f"Segmento {i} fora do corte: {segm['start']:.2f}s -> {segm['end']:.2f}s")
            continue
            
        seg_start = max(segm["start"], start) - start
        seg_end = min(segm["end"], end) - start
        txt = segm["text"]
        
        print(f"Processando segmento {i}: {seg_start:.2f}s -> {seg_end:.2f}s")
        
        # Segmenta o texto em partes menores
        segmentos = segment_text(txt, max_chars=20)
        
        # Calcula a duração total do segmento de áudio
        duracao_total = seg_end - seg_start
        
        # Calcula a duração de cada subsegmento baseado no número de caracteres
        total_chars = sum(len(s) for s in segmentos)
        duracao_base = duracao_total / total_chars
        
        for j, segmento in enumerate(segmentos):
            # Calcula a duração proporcional ao tamanho do texto
            duracao_segmento = (len(segmento) * duracao_base) * 1
            
            # Calcula o tempo de início e fim para cada subsegmento
            if j == 0:
                subseg_start = seg_start
            else:
                subseg_start = seg_start + sum(len(s) * duracao_base * 1 for s in segmentos[:j])
            
            subseg_end = subseg_start + duracao_segmento

            segmento_destacado = highlight_keywords(segmento)

            try:
                legenda = create_animated_text(
                    segmento_destacado,
                    duracao_segmento,
                    font_path,
                    fontsize,
                    video_area_width,
                    ("center", video_area_height - fontsize - margin_bottom)
                )

                legenda = legenda.set_start(max(0, subseg_start - 0))
                legendas.append(legenda)
            except Exception as e:
                print(f"Erro ao criar legenda: {segmento[:50]}... | Erro: {e}")
                print(f"Detalhes do erro: {str(e)}")
                continue

    # Cria o template com header e footer
    template = create_template_clip(final_width, final_height, clip.duration)
    
    # Posiciona o vídeo com legendas na área central do template
    video_with_subtitles = mp.CompositeVideoClip([clip] + legendas, 
                                                size=(video_area_width, video_area_height))
    video_with_subtitles = video_with_subtitles.set_position((20, header_height))  # 20px de margem
    
    # Combina template com vídeo
    final = mp.CompositeVideoClip([template, video_with_subtitles], 
                                size=(final_width, final_height))

    safe_hook = sanitize_filename(highlight['hook'])
    outfile = Path(out_dir) / f"{safe_hook}.mp4"

    final.write_videofile(str(outfile), 
        codec="libx264", 
        fps=30, 
        preset="ultrafast",
        ffmpeg_params=[
            "-profile:v", "main", 
            "-pix_fmt", "yuv420p",
            "-vf", "format=yuv420p"
        ],
        audio_codec="aac"
    )

    clip.close()
    final.close()
    template.close()

    return outfile