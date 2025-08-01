# modules/editor.py
from pathlib import Path
import moviepy.editor as mp
from PIL import Image, ImageEnhance
import re
import unicodedata
import os
import json
import numpy as np
from .video_optimizer import create_optimized_write_params, print_optimization_info, create_fallback_params

def sanitize_filename(name, max_length=50):
    # Remove acentos
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    # Remove caracteres especiais
    name = re.sub(r'[^a-zA-Z0-9_\- ]', '', name)
    # Substitui espaços por underline
    name = name.replace(' ', '_')
    # Limita o tamanho
    return name[:max_length]

def create_video_directory(base_clips_dir: str, video_info: dict) -> Path:
    """
    Cria um diretório específico para os cortes de um vídeo baseado no título
    """
    # Usa o título do vídeo para criar o nome do diretório
    video_title = video_info.get('title', 'video_sem_titulo')
    safe_title = sanitize_filename(video_title, max_length=100)
    
    # Cria o caminho completo
    video_dir = Path(base_clips_dir) / safe_title
    
    # Cria o diretório se não existir
    video_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Diretório criado para o vídeo: {video_dir}")
    return video_dir

def save_clip_metadata(video_dir: Path, clip_filename: str, highlight: dict, video_info: dict, episode_url: str, all_tags: list):
    """
    Salva os metadados do corte em um arquivo JSON
    """
    # Cria a descrição completa
    original_title = video_info.get('title', 'Vídeo Original')
    original_channel = video_info.get('channel', 'Canal Original')
    
    desc = f"""{highlight.get('description', highlight.get('hook', ''))}

🎬 Trecho extraído do episódio: "{original_title}"
📺 Canal original: {original_channel}"""

    tags_string = "#" + " #".join(all_tags)
    desc += f"\n\n{tags_string}"
    
    # Salva o arquivo de metadados
    metadata_file = video_dir / f"{Path(clip_filename).stem}_metadata.txt"
    with open(metadata_file, "w", encoding="utf-8") as f:
        f.write(desc)
    
    print(f"Metadados salvos em: {metadata_file}")
    return metadata_file

def list_video_clips(base_clips_dir: str) -> dict:
    """
    Lista todos os vídeos processados e seus cortes
    """
    clips_info = {}
    base_dir = Path(base_clips_dir)
    
    if not base_dir.exists():
        print(f"Diretório {base_clips_dir} não encontrado")
        return clips_info
    
    for video_dir in base_dir.iterdir():
        if video_dir.is_dir():
            video_name = video_dir.name
            clips_info[video_name] = {
                "video_dir": str(video_dir),
                "clips": [],
                "metadata_files": []
            }
            
            # Lista os arquivos de vídeo e metadados
            for file in video_dir.iterdir():
                if file.suffix == '.mp4':
                    clips_info[video_name]["clips"].append(file.name)
                elif file.suffix == '.json' and 'metadata' in file.name:
                    clips_info[video_name]["metadata_files"].append(file.name)
    
    return clips_info

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

def save_checkpoint(out_dir: str, video_path: str, highlight: dict, transcript: list, video_info: dict = None, episode_url: str = None):
    """Salva o estado atual do processamento"""
    checkpoint = {
        "video_path": video_path,
        "highlight": highlight,
        "transcript": transcript,
        "video_info": video_info or {},
        "episode_url": episode_url,  # Adiciona a URL do episódio ao checkpoint
        "created_at": str(Path().cwd())  # Adiciona timestamp de criação
    }
    checkpoint_path = get_checkpoint_path(out_dir)
    # Cria o diretório se não existir
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checkpoint_path, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)
    print(f"Checkpoint salvo em: {checkpoint_path}")

def load_checkpoint(out_dir: str, episode_url: str = None) -> dict:
    """
    Carrega o último checkpoint salvo com validação da URL do episódio
    
    Args:
        out_dir: Diretório onde está o checkpoint
        episode_url: URL do episódio atual para validação
    
    Returns:
        dict: Checkpoint se válido, None caso contrário
    """
    checkpoint_path = get_checkpoint_path(out_dir)
    
    # Verifica se o arquivo de checkpoint existe
    if not checkpoint_path.exists():
        print("ℹ️  Nenhum checkpoint encontrado")
        return None
    
    try:
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            checkpoint = json.load(f)
        
        # Validação da URL do episódio
        if episode_url and checkpoint.get("episode_url"):
            if checkpoint["episode_url"] != episode_url:
                print(f"⚠️  Checkpoint inválido: URL do episódio não confere")
                print(f"   Checkpoint: {checkpoint['episode_url']}")
                print(f"   Atual: {episode_url}")
                return None
            else:
                print(f"✅ Checkpoint válido encontrado para o episódio")
        elif episode_url and not checkpoint.get("episode_url"):
            print(f"⚠️  Checkpoint sem URL do episódio - considerando inválido para segurança")
            return None
        elif not episode_url:
            print(f"ℹ️  Carregando checkpoint sem validação de URL")
        
        # Validação adicional: verifica se o arquivo de vídeo ainda existe
        video_path = Path(checkpoint.get("video_path", ""))
        if not video_path.exists():
            print(f"⚠️  Checkpoint inválido: arquivo de vídeo não encontrado: {video_path}")
            return None
        
        return checkpoint
        
    except (json.JSONDecodeError, KeyError, Exception) as e:
        print(f"❌ Erro ao carregar checkpoint: {e}")
        return None

def validate_checkpoint_for_episode(out_dir: str, episode_url: str) -> dict:
    """
    Valida especificamente se existe um checkpoint válido para o episódio atual
    
    Args:
        out_dir: Diretório onde está o checkpoint
        episode_url: URL do episódio para validação
    
    Returns:
        dict: Checkpoint se válido para o episódio, None caso contrário
    """
    return load_checkpoint(out_dir, episode_url)

def clear_checkpoint(out_dir: str):
    """Remove o arquivo de checkpoint"""
    checkpoint_path = get_checkpoint_path(out_dir)
    if checkpoint_path.exists():
        checkpoint_path.unlink()
        print("Checkpoint removido")
    else:
        print("ℹ️  Nenhum checkpoint encontrado para remoção")

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

def create_template_clip(width: int, height: int, duration: float, video_format: str = "horizontal", 
                        video_position: tuple = None, video_size: tuple = None) -> mp.VideoClip:
    """
    Cria um template com header e footer baseado no molde fornecido.
    
    Args:
        width: Largura do template
        height: Altura do template
        duration: Duração do template
        video_format: "horizontal", "vertical", ou "square" para ajustar proporções
        video_position: (x, y) da posição do vídeo no template
        video_size: (width, height) do tamanho do vídeo no template
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
    
    # Se temos informações do vídeo, calcula posições dinâmicas
    if video_position and video_size:
        video_x, video_y = video_position
        video_w, video_h = video_size
        
        # Calcula espaços disponíveis
        space_above = video_y
        space_below = height - (video_y + video_h)
        
        # Header se posiciona muito próximo à borda superior do vídeo
        header_height = max(int(space_above * 0.4), int(height * 0.06))  # Mínimo 6% da altura total
        header_y = video_y - header_height - 5  # 5px acima da borda superior do vídeo
        
        # Footer se centraliza no espaço inferior
        footer_height = max(int(space_below * 0.7), int(height * 0.08))  # Mínimo 8% da altura total
        footer_y = video_y + video_h + (space_below - footer_height) // 2
        
        # Linhas de separação contornam exatamente o vídeo
        top_line_y = video_y - 2  # 2px acima da borda superior
        bottom_line_y = video_y + video_h  # 2px abaixo da borda inferior
        
    else:
        # Fallback para quando não temos informações do vídeo
        if video_format == "vertical":
            header_height = int(height * 0.12)
            footer_height = int(height * 0.08)
        elif video_format == "square":
            header_height = int(height * 0.13)
            footer_height = int(height * 0.09)
        else:  # horizontal
            header_height = int(height * 0.15)
            footer_height = int(height * 0.10)
        
        header_y = 0
        footer_y = height - footer_height
        top_line_y = header_height - 2
        bottom_line_y = height - footer_height
    
    # Cria header
    header_elements = []
    
    # Logo circular "CV"
    logo_size = int(header_height * 0.6)
    logo_x = int(width * 0.05)
    logo_y = header_y + header_height // 2
    
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
    title_y = header_y + header_height // 2 - int(header_height * 0.15)
    
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
    
    # Linha superior do header (contorna o vídeo)
    line_clip = mp.ColorClip(size=(width, 2), color=[100, 150, 255], duration=duration)
    line_clip = line_clip.set_position((0, top_line_y))
    header_elements.append(line_clip)
    
    # Cria footer
    footer_elements = []
    
    # Linha inferior do footer (contorna o vídeo)
    footer_line_clip = mp.ColorClip(size=(width, 2), color=[100, 150, 255], duration=duration)
    footer_line_clip = footer_line_clip.set_position((0, bottom_line_y))
    footer_elements.append(footer_line_clip)
    
    # Texto do footer
    footer_text = "Se inscreva • Dé o like • @clipverso-ofc"
    footer_text_y = footer_y + footer_height // 2
    
    # Calcula tamanho da fonte proporcional ao espaço disponível
    # Garante que o texto caiba na largura disponível
    max_fontsize = min(int(footer_height * 0.4), int(width * 0.03))  # Máximo 4% da altura ou 3% da largura
    footer_text_clip = mp.TextClip(footer_text, fontsize=max_fontsize, 
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
        out_dir: str = "clips",
        video_info: dict = None,
        optimization_config: dict = None,
        content_speed: float = 1.25,
        preserve_pitch: bool = True,
        cutting_duration: int = 61,
        crop_mode: str = "fit"
    ) -> Path:
    """
    Recorta, converte para vertical 9:16, gera legendas dinâmicas estilizadas e devolve o caminho final.
    Garante que o clipe tenha no mínimo 1 minuto de duração.
    
    Args:
        crop_mode: "fit" para mostrar todo o conteúdo, "center" para recortar ao centro
    """
    seg = transcript[highlight["idx"]]
    
    # Mostra informações de otimização
    print_optimization_info()
    
    # Se video_info foi fornecido, cria diretório específico para o vídeo
    if video_info:
        video_dir = create_video_directory(out_dir, video_info)
    else:
        video_dir = Path(out_dir)
        video_dir.mkdir(exist_ok=True)

    clip = mp.VideoFileClip(video_path)
    video_duration = clip.duration

    # Define início e fim do corte
    start = seg["start"]
    end = seg["end"]
    min_duration = cutting_duration*content_speed  # 1 minuto e 1 segundos
    if end - start < min_duration:
        end = min(start + min_duration, video_duration)

    # Recorta o trecho
    clip = clip.subclip(start, end)
    
    # Aplica velocidade configurável ao conteúdo do short
    original_duration = end - start
    if content_speed != 1.0:
        if preserve_pitch and content_speed <= 2.0:  # FFmpeg atempo tem limite de 2x
            # Separa áudio e vídeo para processar separadamente
            video_clip = clip.without_audio()
            audio_clip = clip.audio
            
            # Acelera apenas o vídeo
            video_clip = video_clip.speedx(content_speed)
            
            # Processa o áudio para manter o pitch original
            if audio_clip is not None:
                try:
                    # Usa FFmpeg diretamente no áudio do clip
                    import tempfile
                    import subprocess
                    
                    # Cria arquivo temporário para o áudio
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                        temp_audio_path = temp_audio.name
                    
                    # Salva o áudio original
                    audio_clip.write_audiofile(temp_audio_path, verbose=False, logger=None)
                    
                    # Cria arquivo temporário para o áudio processado
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio_fast:
                        temp_audio_fast_path = temp_audio_fast.name
                    
                    # Usa FFmpeg para acelerar mantendo pitch
                    cmd = [
                        'ffmpeg', '-y',  # Sobrescreve arquivo de saída
                        '-i', temp_audio_path,
                        '-filter:a', f'atempo={content_speed}',
                        '-ar', '44100',  # Taxa de amostragem
                        temp_audio_fast_path
                    ]
                    
                    subprocess.run(cmd, check=True, capture_output=True)
                    
                    # Carrega o áudio processado
                    audio_fast = mp.AudioFileClip(temp_audio_fast_path)
                    
                    # Combina vídeo acelerado com áudio processado
                    clip = video_clip.set_audio(audio_fast)
                    
                    print(f"⚡ Velocidade aplicada: {content_speed}x (pitch preservado)")
                    print(f"   • Duração original: {original_duration:.2f}s -> nova: {clip.duration:.2f}s")
                    
                except Exception as e:
                    print(f"⚠️ Erro ao processar áudio com FFmpeg: {e}")
                    print("   • Usando método padrão (pitch será alterado)")
                    clip = clip.speedx(content_speed)
                finally:
                    # Limpa arquivos temporários de forma mais robusta
                    import os
                    import time
                    
                    # Aguarda um pouco para garantir que os arquivos foram liberados
                    time.sleep(0.2)
                    
                    for temp_file in [temp_audio_path, temp_audio_fast_path]:
                        try:
                            if os.path.exists(temp_file):
                                os.unlink(temp_file)
                        except (PermissionError, OSError):
                            # Se não conseguir deletar, não é crítico
                            pass
            else:
                # Se não há áudio, apenas acelera o vídeo
                clip = video_clip
                print(f"⚡ Velocidade aplicada: {content_speed}x (vídeo sem áudio)")
        else:
            # Método padrão (altera pitch)
            clip = clip.speedx(content_speed)
            pitch_status = "pitch alterado" if not preserve_pitch else "pitch alterado (velocidade > 2x)"
            print(f"⚡ Velocidade aplicada: {content_speed}x ({pitch_status})")
            print(f"   • Duração original: {original_duration:.2f}s -> nova: {clip.duration:.2f}s")
        
        new_duration = clip.duration
    else:
        new_duration = original_duration
        print(f"⚡ Velocidade normal: 1.0x (duração: {original_duration:.2f}s)")

    # Define dimensões finais do template
    final_width = 1080
    final_height = 1920
    
    # Calcula dimensões das seções do template (serão ajustadas baseadas no formato)
    video_area_width = final_width - 40  # Margem de 20px de cada lado
    
    # Análise inteligente do formato do vídeo original
    original_w, original_h = clip.size
    original_aspect_ratio = original_w / original_h
    
    print(f"📐 Análise do vídeo original: {original_w}x{original_h} (proporção: {original_aspect_ratio:.2f})")
    
    # Função auxiliar para calcular dimensões do template baseadas no formato
    def get_template_dimensions(format_type):
        if format_type == "vertical":
            header_height = int(final_height * 0.12)  # 12% para header
            footer_height = int(final_height * 0.08)  # 8% para footer
        elif format_type == "square":
            header_height = int(final_height * 0.13)  # 13% para header
            footer_height = int(final_height * 0.09)  # 9% para footer
        else:  # horizontal
            header_height = int(final_height * 0.15)  # 15% para header
            footer_height = int(final_height * 0.10)  # 10% para footer
        
        video_area_height = final_height - header_height - footer_height
        return header_height, footer_height, video_area_height
    
    # Define estratégia baseada na proporção original
    video_format = "horizontal"  # Padrão
    
    if original_aspect_ratio > 1.5:  # Vídeo horizontal (16:9, 4:3, etc.)
        if crop_mode == "fit":
            print("🔄 Estratégia: Vídeo horizontal - mostrar todo conteúdo lateral")
        else:
            print("🔄 Estratégia: Vídeo horizontal - recorte ao centro")
        
        video_format = "horizontal"
        
        # Calcula dimensões do template para vídeo horizontal
        header_height, footer_height, video_area_height = get_template_dimensions(video_format)
        
        if crop_mode == "fit":
            # Redimensiona para caber toda a largura na área disponível
            clip = clip.resize(width=video_area_width)
            w, h = clip.size
            
            # Se a altura for maior que a área disponível, ajusta proporcionalmente
            if h > video_area_height:
                scale_factor = video_area_height / h
                new_width = int(w * scale_factor)
                clip = clip.resize(width=new_width, height=video_area_height)
                w, h = clip.size
            
            # Centraliza verticalmente na área disponível
            y_offset = (video_area_height - h) // 2
            video_y = header_height + y_offset
            clip = clip.set_position((20, video_y))
        else:  # crop_mode == "center"
            # Redimensiona para caber toda a altura na área disponível
            clip = clip.resize(height=video_area_height)
            w, h = clip.size
            
            # Se a largura for maior que a área disponível, corta as laterais
            if w > video_area_width:
                x_center = w // 2
                y_center = h // 2
                clip = clip.crop(x_center=x_center, y_center=y_center, 
                                width=video_area_width, height=video_area_height)
                w, h = clip.size
            
            # Centraliza na área disponível
            x_offset = (video_area_width - w) // 2
            y_offset = (video_area_height - h) // 2
            video_y = header_height + y_offset
            clip = clip.set_position((20 + x_offset, video_y))
        
    elif original_aspect_ratio < 0.8:  # Vídeo vertical (9:16, 3:4, etc.)
        print("🔄 Estratégia: Vídeo vertical - adaptar molde para aproveitar espaço")
        video_format = "vertical"
        
        # Calcula dimensões do template para vídeo vertical
        header_height, footer_height, video_area_height = get_template_dimensions(video_format)
        
        # Redimensiona para caber toda a altura na área disponível
        clip = clip.resize(height=video_area_height)
        w, h = clip.size
        
        # Se a largura for maior que a área disponível, ajusta proporcionalmente
        if w > video_area_width:
            scale_factor = video_area_width / w
            new_height = int(h * scale_factor)
            clip = clip.resize(width=video_area_width, height=new_height)
            w, h = clip.size
        
        # Centraliza horizontalmente na área disponível
        x_offset = (video_area_width - w) // 2
        video_y = header_height
        clip = clip.set_position((20 + x_offset, video_y))
        
    else:  # Vídeo quadrado ou próximo do quadrado
        print("🔄 Estratégia: Vídeo quadrado - ajuste proporcional")
        video_format = "square"
        
        # Calcula dimensões do template para vídeo quadrado
        header_height, footer_height, video_area_height = get_template_dimensions(video_format)
        
        # Redimensiona para caber na área disponível mantendo proporção
        if original_aspect_ratio > 1:  # Ligeiramente horizontal
            clip = clip.resize(width=video_area_width)
            w, h = clip.size
            if h > video_area_height:
                scale_factor = video_area_height / h
                new_width = int(w * scale_factor)
                clip = clip.resize(width=new_width, height=video_area_height)
                w, h = clip.size
            y_offset = (video_area_height - h) // 2
            video_y = header_height + y_offset
            clip = clip.set_position((20, video_y))
        else:  # Ligeiramente vertical
            clip = clip.resize(height=video_area_height)
            w, h = clip.size
            if w > video_area_width:
                scale_factor = video_area_width / w
                new_height = int(h * scale_factor)
                clip = clip.resize(width=video_area_width, height=new_height)
                w, h = clip.size
            x_offset = (video_area_width - w) // 2
            video_y = header_height
            clip = clip.set_position((20 + x_offset, video_y))
    
    # Garante dimensões pares
    final_w, final_h = clip.size
    if final_w % 2 != 0 or final_h % 2 != 0:
        new_w = final_w // 2 * 2
        new_h = final_h // 2 * 2
        clip = clip.resize(newsize=(new_w, new_h))
    
    # Usa as posições calculadas durante o posicionamento
    video_x = 20  # Posição padrão X (já calculada acima)
    # video_y já foi calculada durante o posicionamento em cada estratégia
    
    print(f"✅ Vídeo adaptado: {final_w}x{final_h} na área de conteúdo")
    print(f"   • Posição: ({video_x}, {video_y})")

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
    
    # Filtra apenas segmentos dentro do corte para otimizar
    relevant_segments = [
        segm for segm in transcript 
        if not (segm["end"] <= start or segm["start"] >= end)
    ]
    
    print(f"Processando {len(relevant_segments)} segmentos relevantes...")
    for i, segm in enumerate(relevant_segments):
            
        # Calcula tempos originais do segmento
        seg_start_original = max(segm["start"], start) - start
        seg_end_original = min(segm["end"], end) - start
        
        # Ajusta tempos para a velocidade aplicada
        seg_start = seg_start_original / content_speed
        seg_end = seg_end_original / content_speed
        
        txt = segm["text"]
        
        print(f"Processando segmento {i}: {seg_start_original:.2f}s -> {seg_end_original:.2f}s (ajustado: {seg_start:.2f}s -> {seg_end:.2f}s)")
        
        # Segmenta o texto em partes menores
        segmentos = segment_text(txt, max_chars=20)
        
        # Calcula a duração total do segmento de áudio (ajustada)
        duracao_total = seg_end - seg_start
        
        # Calcula a duração de cada subsegmento baseado no número de caracteres
        total_chars = sum(len(s) for s in segmentos)
        duracao_base = duracao_total / total_chars
        
        for j, segmento in enumerate(segmentos):
            # Calcula a duração proporcional ao tamanho do texto
            duracao_segmento = len(segmento) * duracao_base
            
            # Calcula o tempo de início e fim para cada subsegmento (ajustado)
            if j == 0:
                subseg_start = seg_start
            else:
                subseg_start = seg_start + sum(len(s) * duracao_base for s in segmentos[:j])
            
            subseg_end = subseg_start + duracao_segmento

            segmento_destacado = highlight_keywords(segmento)

            try:
                # Calcula a posição da legenda para acompanhar exatamente a borda do vídeo
                # As legendas aparecem logo abaixo da borda inferior do vídeo
                video_bottom = video_y + final_h
                legenda_y = video_bottom + 10  # 10px de margem abaixo da borda do vídeo
                
                # Se a legenda ficaria muito baixa, posiciona logo acima da borda superior
                if legenda_y + fontsize > final_height - 50:  # 50px de margem do fundo
                    legenda_y = video_y - fontsize - 10  # 10px acima da borda superior
                
                legenda = create_animated_text(
                    segmento_destacado,
                    duracao_segmento,
                    font_path,
                    fontsize,
                    final_width,  # Usa a largura total do template
                    ("center", legenda_y)
                )

                legenda = legenda.set_start(max(0, subseg_start - 0))
                legendas.append(legenda)
            except Exception as e:
                print(f"Erro ao criar legenda: {segmento[:50]}... | Erro: {e}")
                print(f"Detalhes do erro: {str(e)}")
                continue

    # Cria o template com header e footer adaptado ao formato do vídeo
    # Passa informações da posição e tamanho do vídeo para posicionamento dinâmico
    video_pos = (video_x, video_y)  # Usa as posições capturadas anteriormente
    video_sz = (final_w, final_h)  # Usa o tamanho final do vídeo
    
    template = create_template_clip(final_width, final_height, clip.duration, video_format, 
                                  video_position=video_pos, video_size=video_sz)
    
    # Posiciona o vídeo com legendas na área central do template
    # O vídeo já está posicionado corretamente, então apenas combina com as legendas
    video_with_subtitles = mp.CompositeVideoClip([clip] + legendas, 
                                                size=(final_width, final_height))
    # O vídeo já tem sua posição definida, então apenas centraliza o composite
    video_with_subtitles = video_with_subtitles.set_position((0, 0))
    
    # Combina template com vídeo
    final = mp.CompositeVideoClip([template, video_with_subtitles], 
                                size=(final_width, final_height))

    safe_hook = sanitize_filename(highlight['hook'])
    outfile = video_dir / f"{safe_hook}.mp4"

    # Usa parâmetros otimizados
    write_params = create_optimized_write_params(
        use_gpu=optimization_config["use_gpu"],
        quality=optimization_config["quality"]
    )
    
    print(f"🎬 Renderizando com otimizações: {write_params['codec']}")
    
    try:
        final.write_videofile(str(outfile), **write_params)
    except Exception as e:
        if "h264_amf" in str(write_params.get('codec', '')) and "Invalid argument" in str(e):
            print("⚠️ Erro no codec AMD, usando fallback para CPU...")
            fallback_params = create_fallback_params()
            print(f"🔄 Renderizando com fallback: {fallback_params['codec']}")
            final.write_videofile(str(outfile), **fallback_params)
        else:
            # Re-raise se não for erro de codec AMD
            raise e

    clip.close()
    final.close()
    template.close()

    return outfile

def get_upload_checkpoint_path(video_dir: str) -> Path:
    """Retorna o caminho do arquivo de checkpoint de upload para o diretório do vídeo"""
    return Path(video_dir) / "upload_checkpoint.json"

def save_upload_checkpoint(video_dir: str, episode_url: str, generated_clips: list):
    """
    Salva checkpoint com informações de todos os cortes gerados para upload posterior
    """
    checkpoint_path = get_upload_checkpoint_path(video_dir)
    
    # Adiciona campos de status de upload se não existirem
    for clip in generated_clips:
        if "uploaded" not in clip:
            clip["uploaded"] = False
        if "uploaded_at" not in clip:
            clip["uploaded_at"] = None
    
    checkpoint_data = {
        "episode_url": episode_url,
        "generated_clips": generated_clips,
        "total_clips": len(generated_clips),
        "created_at": str(Path().cwd() / "upload_checkpoint.json")
    }
    
    with open(checkpoint_path, "w", encoding="utf-8") as f:
        json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Checkpoint de upload salvo: {checkpoint_path}")
    print(f"   • {len(generated_clips)} cortes prontos para upload")
    return checkpoint_path


def load_upload_checkpoint(video_dir: str) -> dict:
    """
    Carrega checkpoint de upload se existir para o diretório do vídeo
    """
    checkpoint_path = get_upload_checkpoint_path(video_dir)
    
    if not checkpoint_path.exists():
        return None
    
    try:
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            checkpoint_data = json.load(f)
        print(f"✅ Checkpoint de upload carregado: {checkpoint_path}")
        print(f"   • {checkpoint_data['total_clips']} cortes encontrados")
        return checkpoint_data
    except Exception as e:
        print(f"❌ Erro ao carregar checkpoint de upload: {e}")
        return None


def clear_upload_checkpoint(video_dir: str):
    """
    Remove checkpoint de upload após conclusão para o diretório do vídeo
    """
    checkpoint_path = get_upload_checkpoint_path(video_dir)
    if checkpoint_path.exists():
        checkpoint_path.unlink()
        print(f"✅ Checkpoint de upload removido: {checkpoint_path}")
    else:
        print("ℹ️ Nenhum checkpoint de upload encontrado para remover")