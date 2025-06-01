# modules/editor.py
from pathlib import Path
import moviepy.editor as mp
from PIL import Image, ImageEnhance
import re
import unicodedata
import os
import json

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

def save_checkpoint(out_dir: str, video_path: str, highlight: dict, transcript: list):
    """Salva o estado atual do processamento"""
    checkpoint = {
        "video_path": video_path,
        "highlight": highlight,
        "transcript": transcript
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

def segment_text(text: str, max_chars: int = 50) -> list:
    """
    Segmenta o texto em partes menores respeitando pontuação e pausas naturais.
    """
    # Pontuações que indicam pausa natural
    pausas = ['.', '!', '?', ':', ';', ',']
    
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

def make_clip(video_path: str, highlight: dict, transcript: list,
              out_dir: str = "clips") -> Path:
    """
    Recorta, converte para vertical 9:16, gera legendas dinâmicas estilizadas e devolve o caminho final.
    Garante que o clipe tenha no mínimo 1 minuto de duração.
    """
    seg = transcript[highlight["idx"]]
    Path(out_dir).mkdir(exist_ok=True)

    # Carrega o vídeo
    print(f"Carregando vídeo: {video_path}")
    clip = mp.VideoFileClip(video_path)
    video_duration = clip.duration
    print(f"Duração do vídeo: {video_duration:.2f}s")

    # Define início e fim do corte
    start = seg["start"]
    end = seg["end"]
    min_duration = 60  # 1 minuto
    if end - start < min_duration:
        end = min(start + min_duration, video_duration)
    print(f"Corte: {start:.2f}s -> {end:.2f}s")
    
    # Recorta o trecho
    clip = clip.subclip(start, end)
    
    # Redimensiona para 1080x1920 (vertical)
    print("Redimensionando para formato vertical...")
    # Primeiro redimensiona pela altura para 1920px
    clip = clip.resize(height=1920)
    w, h = clip.size
    # Calcula o centro e corta as laterais para manter proporção 9:16
    x_center = w/2
    y_center = h/2
    width = 1080  # Largura fixa para proporção 9:16
    height = 1920
    clip = clip.crop(x_center=x_center, y_center=y_center, width=width, height=height)
    final_w, final_h = clip.size
    if final_w % 2 != 0 or final_h % 2 != 0:
        new_w = final_w // 2 * 2
        new_h = final_h // 2 * 2
        clip = clip.resize(newsize=(new_w, new_h))
    print(f"Tamanho final: {final_w}x{final_h}")

    # Gera legendas dinâmicas sincronizadas
    print("Gerando legendas...")
    font_path = get_font_path()
    fontsize = int(0.06 * height)  # 6% da altura
    margin_bottom = int(0.15 * height)  # Aumentei a margem para subir a legenda
    legendas = []
    
    # Testa se a fonte está funcionando
    try:
        test_clip = mp.TextClip("Teste", fontsize=fontsize, font=font_path, color="white")
        test_clip.close()
        print("Fonte testada com sucesso")
    except Exception as e:
        print(f"Erro ao testar fonte: {e}")
        print("Usando fonte padrão do sistema")
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
        segmentos = segment_text(txt)
        duracao_segmento = (seg_end - seg_start) / len(segmentos)
        
        for j, segmento in enumerate(segmentos):
            # Calcula o tempo de início e fim para cada subsegmento
            subseg_start = seg_start + (j * duracao_segmento)
            subseg_end = subseg_start + duracao_segmento
            
            # Legenda estilizada
            try:
                legenda = mp.TextClip(segmento, 
                    fontsize=fontsize, 
                    font=font_path, 
                    color="white",
                    stroke_color="black", 
                    stroke_width=2, 
                    method="caption", 
                    size=(width-80, None))
                    
                # Define a duração do TextClip antes de posicionar
                legenda = legenda.set_duration(duracao_segmento)
                legenda = legenda.set_start(subseg_start) \
                    .set_position(("center", height - fontsize - margin_bottom))
                    
                print(f"Legenda criada: {segmento[:50]}...")
                legendas.append(legenda)
            except Exception as e:
                print(f"Erro ao criar legenda: {segmento[:50]}... | Erro: {e}")
                print(f"Detalhes do erro: {str(e)}")
                continue
    
    print(f"Total de legendas criadas: {len(legendas)}")
    
    if not legendas:
        print("AVISO: Nenhuma legenda foi criada!")
        print("Verifique se há segmentos de texto dentro do corte e se a fonte está funcionando corretamente.")
    
    # Combina vídeo e legendas
    print("Combinando elementos...")
    elementos = [clip] + legendas
    final = mp.CompositeVideoClip(elementos, size=(width, height))
    
    # Salva o arquivo com nome seguro
    safe_hook = sanitize_filename(highlight['hook'])
    outfile = Path(out_dir) / f"{safe_hook}.mp4"
    print(f"Salvando vídeo em: {outfile}")
    final.write_videofile(str(outfile), 
                         codec="libx264", 
                         fps=30, 
                         preset="ultrafast",
                         ffmpeg_params=[
                             "-profile:v", "main", 
                             "-pix_fmt", "yuv420p",
                             "-vf", "format=yuv420p"  # Força o formato de cor correto
                         ],
                         audio_codec="aac")
    
    # Limpa os recursos
    clip.close()
    final.close()
    
    return outfile