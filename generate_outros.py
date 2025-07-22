#!/usr/bin/env python3
"""
Gerador de outros para ClipVerso
Cria 3 variações de outros com TTS, animações e textos engajantes
"""

import os
import random
import numpy as np
import moviepy.editor as mp
from moviepy.editor import VideoClip, AudioClip, CompositeVideoClip, TextClip, ColorClip
from pathlib import Path
import openai
from dotenv import load_dotenv
import json

# Importa configuração do MoviePy
from modules import moviepy_config

# Carrega variáveis de ambiente
load_dotenv()

# Configuração OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

class OutroGenerator:
    def __init__(self):
        self.width = 1080
        self.height = 1920
        self.fps = 30
        self.duration = 5.0
        self.audio_sample_rate = 48000
        
        # Diretórios
        self.assets_dir = Path("assets/outros")
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuração da fonte
        self.font_path = r"C:\Users\vidal\Documents\podcast_cuts\fonts\Roboto-Bold.ttf"
        if not os.path.exists(self.font_path):
            print(f"⚠️  Fonte não encontrada: {self.font_path}")
            self.font_path = "Arial-Bold"  # Fallback
        else:
            print(f"✅ Usando fonte: {self.font_path}")
        
        # Configurações de texto
        self.texts = [
            "Curtiu? Deixa o like 👍",
            "Se inscreva no canal",
            "Qual a sua opinião? Deixe nos comentários",
            "Compartilhe com os amigos",
            "Ative o sininho 🔔"
        ]
        
        # Configurações de TTS
        self.tts_scripts = [
            "Curtiu o vídeo? Deixa o like e se inscreva no canal! Sua opinião é muito importante, deixe nos comentários.",
            "Se você gostou, não esquece de dar like e se inscrever! Compartilha com os amigos e deixa sua opinião nos comentários.",
            "Gostou do conteúdo? Deixa o like, se inscreve no canal e ativa o sininho! Sua opinião nos comentários é fundamental."
        ]
    
    def create_background(self):
        """Cria o fundo com gradiente baseado no molde"""
        def make_frame(t):
            frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            
            # Gradiente horizontal azul para roxo
            for x in range(self.width):
                blue_ratio = 1 - (x / self.width)
                purple_ratio = x / self.width
                
                # Cores base (azul escuro e roxo escuro)
                blue_color = np.array([30, 30, 100])
                purple_color = np.array([80, 30, 100])
                
                # Mistura as cores
                color = (blue_color * blue_ratio + purple_color * purple_ratio).astype(np.uint8)
                frame[:, x] = color
            
            return frame
        
        return VideoClip(make_frame, duration=self.duration)
    
    def create_header(self):
        """Cria o header com logo e branding"""
        header_height = int(self.height * 0.15)
        elements = []
        
        # Logo circular "CV"
        logo_size = int(header_height * 0.6)
        logo_x = int(self.width * 0.05)
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
                        
                        blue_color = np.array([100, 150, 255])
                        purple_color = np.array([200, 100, 255])
                        color = (blue_color * blue_ratio + purple_color * purple_ratio).astype(np.uint8)
                        frame[y, x] = color
            return frame
        
        logo_clip = VideoClip(make_logo_frame, duration=self.duration)
        logo_clip = logo_clip.set_position((logo_x, logo_y - logo_size//2))
        elements.append(logo_clip)
        
        # Texto "CV" no logo
        cv_text = TextClip("CV", fontsize=int(logo_size * 0.4), font=self.font_path, 
                          color="white", stroke_color="black", stroke_width=1)
        cv_text = cv_text.set_position((logo_x + logo_size//2 - cv_text.w//2, 
                                       logo_y - cv_text.h//2))
        cv_text = cv_text.set_duration(self.duration)
        elements.append(cv_text)
        
        # Título "CLIPVERSO"
        title_x = logo_x + logo_size + int(self.width * 0.03)
        title_y = header_height // 2 - int(header_height * 0.15)
        
        title_clip = TextClip("CLIPVERSO", fontsize=int(header_height * 0.25), 
                             font=self.font_path, color="white")
        title_clip = title_clip.set_position((title_x, title_y))
        title_clip = title_clip.set_duration(self.duration)
        elements.append(title_clip)
        
        # Subtitle "CANAL DE CORTES"
        subtitle_y = title_y + int(header_height * 0.25)
        subtitle_clip = TextClip("CANAL DE CORTES", fontsize=int(header_height * 0.15), 
                                font=self.font_path, color="#87CEEB")
        subtitle_clip = subtitle_clip.set_position((title_x, subtitle_y))
        subtitle_clip = subtitle_clip.set_duration(self.duration)
        elements.append(subtitle_clip)
        
        # Linha superior do header
        line_y = header_height - 2
        line_clip = ColorClip(size=(self.width, 2), color=[100, 150, 255], duration=self.duration)
        line_clip = line_clip.set_position((0, line_y))
        elements.append(line_clip)
        
        return elements
    
    def create_footer(self):
        """Cria o footer com call to action"""
        header_height = int(self.height * 0.15)
        footer_height = int(self.height * 0.10)
        video_area_height = self.height - header_height - footer_height
        
        elements = []
        
        # Linha inferior do footer
        footer_line_y = header_height + video_area_height
        footer_line_clip = ColorClip(size=(self.width, 2), color=[100, 150, 255], duration=self.duration)
        footer_line_clip = footer_line_clip.set_position((0, footer_line_y))
        elements.append(footer_line_clip)
        
        # Texto do footer
        footer_text = "Se inscreva • Dé o like • @clipverso-ofc"
        footer_text_y = footer_line_y + int(footer_height * 0.3)
        footer_text_clip = TextClip(footer_text, fontsize=int(footer_height * 0.3), 
                                   font=self.font_path, color="white")
        footer_text_clip = footer_text_clip.set_position(("center", footer_text_y))
        footer_text_clip = footer_text_clip.set_duration(self.duration)
        elements.append(footer_text_clip)
        
        return elements
    
    def create_animated_texts(self):
        """Cria textos animados no centro do vídeo"""
        header_height = int(self.height * 0.15)
        footer_height = int(self.height * 0.10)
        video_area_height = self.height - header_height - footer_height
        
        elements = []
        
        # Seleciona 3 textos aleatórios para animar
        selected_texts = random.sample(self.texts, 3)
        
        for i, text in enumerate(selected_texts):
            # Calcula timing para cada texto
            start_time = i * 1.5  # Cada texto aparece a cada 1.5s
            duration = 1.0
            
            # Cria o texto
            text_clip = TextClip(text, fontsize=60, font=self.font_path, 
                               color="white", stroke_color="black", stroke_width=2)
            
            # Posiciona no centro da área de vídeo
            text_clip = text_clip.set_position(("center", header_height + video_area_height//2))
            
            # Adiciona animações
            text_clip = text_clip.set_start(start_time).set_duration(duration)
            
            # Fade in/out
            text_clip = text_clip.crossfadein(0.2).crossfadeout(0.2)
            
            # Efeito de escala
            def scale_effect(t):
                if t < 0.2:
                    return 0.5 + (t / 0.2) * 0.5  # Scale up
                elif t > 0.8:
                    return 1.0 - ((t - 0.8) / 0.2) * 0.2  # Scale down slightly
                else:
                    return 1.0
            
            text_clip = text_clip.resize(scale_effect)
            
            elements.append(text_clip)
        
        return elements
    
    def generate_tts_audio(self, script: str) -> str:
        """Gera áudio TTS usando OpenAI"""
        try:
            response = openai.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=script,
                speed=1.0
            )
            
            # Salva o áudio temporariamente
            audio_path = self.assets_dir / "temp_tts.mp3"
            with open(audio_path, "wb") as f:
                f.write(response.content)
            
            return str(audio_path)
            
        except Exception as e:
            print(f"Erro ao gerar TTS: {e}")
            return None
    
    def create_outro(self, outro_number: int):
        """Cria um outro completo"""
        print(f"Gerando outro {outro_number}...")
        
        # Seleciona script TTS
        tts_script = self.tts_scripts[outro_number - 1]
        
        # Gera áudio TTS
        print("Gerando áudio TTS...")
        audio_path = self.generate_tts_audio(tts_script)
        
        if not audio_path:
            print("Erro: Não foi possível gerar áudio TTS")
            return None
        
        # Carrega o áudio
        audio_clip = mp.AudioFileClip(audio_path)
        
        # Ajusta duração se necessário
        if audio_clip.duration > self.duration:
            audio_clip = audio_clip.subclip(0, self.duration)
        elif audio_clip.duration < self.duration:
            # Adiciona silêncio no final
            silence_duration = self.duration - audio_clip.duration
            silence = mp.AudioClip(lambda t: 0, duration=silence_duration)
            audio_clip = mp.concatenate_audioclips([audio_clip, silence])
        
        # Cria elementos visuais
        background = self.create_background()
        header_elements = self.create_header()
        footer_elements = self.create_footer()
        animated_texts = self.create_animated_texts()
        
        # Combina todos os elementos
        video_clip = CompositeVideoClip(
            [background] + header_elements + footer_elements + animated_texts,
            size=(self.width, self.height)
        )
        
        # Adiciona áudio
        final_clip = video_clip.set_audio(audio_clip)
        
        # Salva o outro
        output_path = self.assets_dir / f"outro{outro_number}.mp4"
        
        print(f"Renderizando outro {outro_number}...")
        final_clip.write_videofile(
            str(output_path),
            fps=self.fps,
            codec='libx264',
            audio_codec='aac',
            audio_fps=self.audio_sample_rate,
            preset='medium',
            threads=4
        )
        
        # Limpa recursos
        final_clip.close()
        audio_clip.close()
        
        # Remove arquivo temporário (com tratamento de erro)
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
        except PermissionError:
            print(f"⚠️  Não foi possível remover arquivo temporário: {audio_path}")
        except Exception as e:
            print(f"⚠️  Erro ao remover arquivo temporário: {e}")
        
        print(f"✅ Outro {outro_number} gerado: {output_path}")
        return output_path
    
    def generate_all_outros(self):
        """Gera todos os 3 outros"""
        print("🎬 Iniciando geração dos outros do ClipVerso...")
        
        generated_outros = []
        
        for i in range(1, 4):
            outro_path = self.create_outro(i)
            if outro_path:
                generated_outros.append(outro_path)
        
        print(f"\n🎉 Geração concluída! {len(generated_outros)} outros criados:")
        for path in generated_outros:
            print(f"  - {path}")
        
        return generated_outros

def main():
    """Função principal"""
    generator = OutroGenerator()
    generator.generate_all_outros()

if __name__ == "__main__":
    main() 