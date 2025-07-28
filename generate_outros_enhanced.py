#!/usr/bin/env python3
"""
Gerador de outros melhorado para ClipVerso
Cria outros com animações criativas, efeitos visuais e sincronização perfeita com TTS
"""

import os
import random
import numpy as np
import moviepy.editor as mp
from moviepy.editor import VideoClip, AudioClip, CompositeVideoClip, TextClip, ColorClip, ImageClip
from pathlib import Path
import openai
from dotenv import load_dotenv
import json
import math

# Importa configuração do MoviePy
from modules import moviepy_config

# Carrega variáveis de ambiente
load_dotenv()

# Configuração OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

class EnhancedOutroGenerator:
    def __init__(self):
        self.width = 1080
        self.height = 1920
        self.fps = 30
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
        
        # Carrega logo
        self.logo_path = "logo.png"
        if os.path.exists(self.logo_path):
            print(f"✅ Logo carregado: {self.logo_path}")
        else:
            print(f"⚠️  Logo não encontrado: {self.logo_path}")
            self.logo_path = None
        
        # Configurações de texto melhoradas
        self.texts = [
            "Curtiu? Deixa o like 👍",
            "Se inscreva no canal",
            "Qual a sua opinião? Deixe nos comentários",
            "Compartilhe com os amigos",
            "Ative o sininho 🔔"
        ]
        
        # Scripts TTS otimizados para velocidade
        self.tts_scripts = [
            "... E aí, curtiu o vídeo? Deixa o like e se inscreva no canal! Sua opinião é muito importante, deixe nos comentários...",
            "... Se você gostou, não esquece de dar like e se inscrever! Compartilha com os amigos e deixa sua opinião nos comentários...",
            "... Gostou do conteúdo? Deixa o like e se inscreve no canal! Sua opinião nos comentários é fundamental..."
        ]
    
    def create_animated_background(self, duration: float):
        """Cria fundo animado com gradiente dinâmico"""
        def make_frame(t):
            frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            
            # Gradiente animado que se move
            offset = int(t * 50) % self.width  # Movimento suave
            
            for x in range(self.width):
                # Gradiente horizontal com movimento
                pos = (x + offset) % self.width
                blue_ratio = 1 - (pos / self.width)
                purple_ratio = pos / self.width
                
                # Cores base com variação temporal
                blue_color = np.array([30 + int(10 * math.sin(t * 2)), 30, 100 + int(20 * math.sin(t * 1.5))])
                purple_color = np.array([80 + int(15 * math.sin(t * 1.8)), 30, 100 + int(25 * math.sin(t * 2.2))])
                
                # Mistura as cores
                color = (blue_color * blue_ratio + purple_color * purple_ratio).astype(np.uint8)
                frame[:, x] = color
            
            return frame
        
        return VideoClip(make_frame, duration=duration)
    
    def create_animated_logo(self, duration: float):
        """Cria logo animado com efeitos"""
        if not self.logo_path:
            return None
        
        # Carrega a logo
        logo_clip = ImageClip(self.logo_path)
        
        # Redimensiona para tamanho apropriado
        logo_size = int(self.height * 0.08)  # 8% da altura
        logo_clip = logo_clip.resize(height=logo_size)
        
        # Posiciona no canto superior direito
        logo_x = self.width - logo_size - 40
        logo_y = 40
        
        # Adiciona animações
        def logo_animation(t):
            # Efeito de flutuação suave
            float_offset = 5 * math.sin(t * 3)
            # Efeito de rotação sutil
            rotation = 2 * math.sin(t * 2)
            return logo_x, logo_y + float_offset, rotation
        
        logo_clip = logo_clip.set_position((logo_x, logo_y))
        logo_clip = logo_clip.set_duration(duration)
        
        # Adiciona efeito de brilho
        def glow_effect(t):
            glow_intensity = 0.3 + 0.2 * math.sin(t * 4)
            return glow_intensity
        
        return logo_clip
    
    def create_animated_header(self, duration: float):
        """Cria header animado com efeitos visuais"""
        header_height = int(self.height * 0.15)
        elements = []
        
        # Logo circular "CV" com animações
        logo_size = int(header_height * 0.6)
        logo_x = int(self.width * 0.05)
        logo_y = header_height // 2
        
        # Cria logo circular com gradiente animado
        def make_logo_frame(t):
            frame = np.zeros((logo_size, logo_size, 3), dtype=np.uint8)
            center = logo_size // 2
            radius = logo_size // 2 - 5
            
            # Efeito de rotação do gradiente
            rotation_offset = t * 2 * math.pi
            
            for y in range(logo_size):
                for x in range(logo_size):
                    dist = np.sqrt((x - center)**2 + (y - center)**2)
                    if dist <= radius:
                        # Gradiente circular com rotação
                        angle = np.arctan2(y - center, x - center) + rotation_offset
                        ratio = (angle + np.pi) / (2 * np.pi)
                        blue_ratio = 1 - ratio
                        purple_ratio = ratio
                        
                        # Cores com variação temporal
                        blue_color = np.array([100 + int(30 * math.sin(t * 3)), 150 + int(20 * math.sin(t * 2)), 255])
                        purple_color = np.array([200 + int(25 * math.sin(t * 2.5)), 100 + int(15 * math.sin(t * 1.8)), 255])
                        color = (blue_color * blue_ratio + purple_color * purple_ratio).astype(np.uint8)
                        frame[y, x] = color
            return frame
        
        logo_clip = VideoClip(make_logo_frame, duration=duration)
        logo_clip = logo_clip.set_position((logo_x, logo_y - logo_size//2))
        elements.append(logo_clip)
        
        # Texto "CV" no logo com animação
        cv_text = TextClip("CV", fontsize=int(logo_size * 0.4), font=self.font_path, 
                          color="white", stroke_color="black", stroke_width=1)
        cv_text = cv_text.set_position((logo_x + logo_size//2 - cv_text.w//2, 
                                       logo_y - cv_text.h//2))
        cv_text = cv_text.set_duration(duration)
        
        # Adiciona efeito de pulso
        def pulse_effect(t):
            scale = 1.0 + 0.1 * math.sin(t * 6)
            return scale
        
        cv_text = cv_text.resize(pulse_effect)
        elements.append(cv_text)
        
        # Título "CLIPVERSO" com animação de entrada
        title_x = logo_x + logo_size + int(self.width * 0.03)
        title_y = header_height // 2 - int(header_height * 0.15)
        
        title_clip = TextClip("CLIPVERSO", fontsize=int(header_height * 0.25), 
                             font=self.font_path, color="white")
        title_clip = title_clip.set_position((title_x, title_y))
        title_clip = title_clip.set_duration(duration)
        
        # Animação de entrada deslizante
        def slide_in_effect(t):
            if t < 0.5:
                return title_x - 100 + (t * 200), title_y
            else:
                return title_x, title_y
        
        title_clip = title_clip.set_position(slide_in_effect)
        elements.append(title_clip)
        
        # Subtitle "CANAL DE CORTES" com fade in
        subtitle_y = title_y + int(header_height * 0.25)
        subtitle_clip = TextClip("CANAL DE CORTES", fontsize=int(header_height * 0.15), 
                                font=self.font_path, color="#87CEEB")
        subtitle_clip = subtitle_clip.set_position((title_x, subtitle_y))
        subtitle_clip = subtitle_clip.set_duration(duration)
        
        # Fade in
        subtitle_clip = subtitle_clip.crossfadein(1.0)
        elements.append(subtitle_clip)
        
        # Linha superior animada
        line_y = header_height - 2
        def make_line_frame(t):
            frame = np.zeros((2, self.width, 3), dtype=np.uint8)
            for x in range(self.width):
                # Efeito de onda na linha
                wave_offset = int(10 * math.sin(t * 4 + x * 0.02))
                color_intensity = 100 + int(50 * math.sin(t * 3 + x * 0.01))
                frame[:, x] = [color_intensity, 150, 255]
            return frame
        
        line_clip = VideoClip(make_line_frame, duration=duration)
        line_clip = line_clip.set_position((0, line_y))
        elements.append(line_clip)
        
        return elements
    
    def create_animated_footer(self, duration: float):
        """Cria footer animado"""
        header_height = int(self.height * 0.15)
        footer_height = int(self.height * 0.10)
        video_area_height = self.height - header_height - footer_height
        
        elements = []
        
        # Linha inferior animada
        footer_line_y = header_height + video_area_height
        def make_footer_line_frame(t):
            frame = np.zeros((2, self.width, 3), dtype=np.uint8)
            for x in range(self.width):
                # Efeito de onda na linha
                wave_offset = int(8 * math.sin(t * 3 + x * 0.015))
                color_intensity = 100 + int(40 * math.sin(t * 2.5 + x * 0.008))
                frame[:, x] = [color_intensity, 150, 255]
            return frame
        
        footer_line_clip = VideoClip(make_footer_line_frame, duration=duration)
        footer_line_clip = footer_line_clip.set_position((0, footer_line_y))
        elements.append(footer_line_clip)
        
        # Texto do footer com ícones e animação (usando símbolos simples)
        footer_text = "Se inscreva ▶ • Dé o like ♥ • @clipverso-ofc"
        footer_text_y = footer_line_y + int(footer_height * 0.3)
        footer_text_clip = TextClip(footer_text, fontsize=int(footer_height * 0.25), 
                                   font=self.font_path, color="white", stroke_color="black", stroke_width=1,
                                   method="caption", size=(self.width - 40, None))
        footer_text_clip = footer_text_clip.set_position(("center", footer_text_y))
        footer_text_clip = footer_text_clip.set_duration(duration)
        
        # Efeito de fade in melhorado
        footer_text_clip = footer_text_clip.crossfadein(1.0)
        
        # Adiciona efeito de pulso sutil
        def footer_pulse(t):
            scale = 1.0 + 0.03 * math.sin(t * 4)
            return scale
        
        footer_text_clip = footer_text_clip.resize(footer_pulse)
        elements.append(footer_text_clip)
        
        return elements

    def create_animated_icon(self, icon: str, start_time: float, duration: float, y_position: int):
        """Cria ícone animado separado"""
        # Tamanho do ícone
        icon_size = 60
        
        # Cria o ícone
        icon_clip = TextClip(icon, fontsize=icon_size, font=self.font_path,
                           color="white", stroke_color="black", stroke_width=2)
        
        # Posiciona abaixo do texto
        icon_clip = icon_clip.set_position(("center", y_position))
        icon_clip = icon_clip.set_start(start_time).set_duration(duration)
        
        # Animações especiais para ícones
        def icon_animation(t):
            if t < 0.2:
                scale = 0.3 + (t / 0.2) * 0.7  # Aparece pequeno e cresce
                rotation = (t / 0.2) * 360  # Rotação completa
            elif t > 0.8:
                scale = 1.0 - ((t - 0.8) / 0.2) * 0.3  # Diminui sutilmente
                rotation = 0
            else:
                scale = 1.0 + 0.15 * math.sin(t * 8)  # Pulsação mais forte
                rotation = 5 * math.sin(t * 4)  # Rotação sutil
            
            return scale, rotation
        
        # Aplica animações
        icon_clip = icon_clip.resize(lambda t: icon_animation(t)[0])
        icon_clip = icon_clip.rotate(lambda t: icon_animation(t)[1])
        
        # Adiciona efeito de brilho
        def glow_effect(t):
            glow_intensity = 0.8 + 0.2 * math.sin(t * 6)
            return glow_intensity
        
        # Fade in/out
        icon_clip = icon_clip.crossfadein(0.2).crossfadeout(0.2)
        
        return icon_clip
    

    
    def create_particle_effects(self, duration: float):
        """Cria efeitos de partículas flutuantes e elementos visuais"""
        elements = []
        
        # Cria partículas flutuantes (menos para dar destaque às logos)
        for i in range(15):  # Reduzido de 25 para 15
            particle = self.create_single_particle(i, duration)
            elements.append(particle)
        
        # Cria elementos visuais adicionais
        elements.extend(self.create_floating_elements(duration))
        
        return elements
    
    def create_floating_elements(self, duration: float):
        """Cria elementos flutuantes adicionais"""
        elements = []
        
        # Cria mais logos flutuantes (planetas/estrelas do ClipVerso)
        for i in range(12):  # Aumentado de 6 para 12
            logo = self.create_floating_logo(i, duration)
            if logo:  # Só adiciona se a logo foi criada com sucesso
                elements.append(logo)
        
        # Cria linhas de energia (menos para dar destaque às logos)
        for i in range(2):
            energy_line = self.create_energy_line(i, duration)
            elements.append(energy_line)
        
        return elements
    
    def create_floating_logo(self, logo_id, duration: float):
        """Cria logo flutuante animado (planeta/estrela do ClipVerso)"""
        if not self.logo_path or not os.path.exists(self.logo_path):
            print(f"⚠️ Logo não encontrada: {self.logo_path}")
            return None
        
        try:
            # Carrega a logo com verificação
            logo_clip = ImageClip(self.logo_path)
            
            # Verifica se a logo foi carregada corretamente
            if logo_clip.size[0] == 0 or logo_clip.size[1] == 0:
                print(f"⚠️ Logo inválida (tamanho zero): {self.logo_path}")
                return None
            
            # Tamanhos variados para as logos flutuantes (planetas/estrelas)
            sizes = [35, 45, 55, 65, 75, 85, 95, 105]
            logo_size = sizes[logo_id % len(sizes)]
            
            # Redimensiona a logo mantendo proporção
            logo_clip = logo_clip.resize(height=logo_size)
            
            # Define área de movimento (apenas na área do vídeo)
            header_height = int(self.height * 0.15)
            footer_height = int(self.height * 0.10)
            video_area_height = self.height - header_height - footer_height
            
            # Posição inicial aleatória dentro da área do vídeo
            x = random.randint(logo_size//2, self.width - logo_size//2)
            y = random.randint(header_height + logo_size//2, header_height + video_area_height - logo_size//2)
            
            # Posiciona a logo
            logo_clip = logo_clip.set_position((x, y))
            logo_clip = logo_clip.set_duration(duration)
            
            # Animações suaves (movimento de planeta/estrela)
            def logo_animation(t):
                # Movimento orbital suave
                orbit_radius_x = 30 + (logo_id % 3) * 10
                orbit_radius_y = 25 + (logo_id % 2) * 8
                orbit_speed = 0.8 + (logo_id % 4) * 0.3
                
                float_x = x + orbit_radius_x * math.sin(t * orbit_speed + logo_id)
                float_y = y + orbit_radius_y * math.cos(t * orbit_speed * 1.2 + logo_id)
                
                # Mantém dentro dos limites da área do vídeo
                float_x = max(logo_size//2, min(self.width - logo_size//2, float_x))
                float_y = max(header_height + logo_size//2, 
                             min(header_height + video_area_height - logo_size//2, float_y))
                
                return float_x, float_y
            
            logo_clip = logo_clip.set_position(logo_animation)
            
            # Adiciona rotação sutil (como planeta girando)
            def rotation_animation(t):
                rotation = 2 * math.sin(t * 1.5 + logo_id)
                return rotation
            
            logo_clip = logo_clip.rotate(rotation_animation)
            
            # Adiciona efeito de brilho fixo (como estrela)
            logo_clip = logo_clip.set_opacity(0.6)
            
            return logo_clip
            
        except Exception as e:
            print(f"⚠️ Erro ao criar logo flutuante {logo_id}: {e}")
            # Em caso de erro, retorna None em vez de criar quadrado preto
            return None
    
    def create_energy_line(self, line_id, duration: float):
        """Cria linha de energia animada"""
        # Define área de movimento (apenas na área do vídeo)
        header_height = int(self.height * 0.15)
        footer_height = int(self.height * 0.10)
        video_area_height = self.height - header_height - footer_height
        
        # Posição inicial dentro da área do vídeo
        x = random.randint(50, self.width - 50)
        y = random.randint(header_height + 50, header_height + video_area_height - 50)
        
        # Comprimento
        length = random.randint(60, 120)
        
        # Cor
        colors = [(100, 150, 255), (200, 100, 255)]
        color = random.choice(colors)
        
        def make_line_frame(t):
            # Cria frame da linha
            frame = np.zeros((2, length, 3), dtype=np.uint8)
            
            for i in range(length):
                # Efeito de onda na linha
                wave_intensity = 0.6 + 0.4 * math.sin(t * 2.5 + i * 0.08 + line_id)
                frame[:, i] = [int(color[0] * wave_intensity), int(color[1] * wave_intensity), int(color[2] * wave_intensity)]
            
            return frame
        
        line_clip = VideoClip(make_line_frame, duration=duration)
        
        # Posição e rotação animadas (limitadas à área do vídeo)
        def transform_animation(t):
            new_x = x + 20 * math.sin(t * 1.8 + line_id)
            new_y = y + 15 * math.cos(t * 1.5 + line_id)
            rotation = 30 * math.sin(t * 1.2 + line_id)
            
            # Mantém dentro dos limites da área do vídeo
            new_x = max(length//2, min(self.width - length//2, new_x))
            new_y = max(header_height + length//2, 
                       min(header_height + video_area_height - length//2, new_y))
            
            return new_x, new_y, rotation
        
        line_clip = line_clip.set_position(lambda t: (transform_animation(t)[0], transform_animation(t)[1]))
        line_clip = line_clip.rotate(lambda t: transform_animation(t)[2])
        
        return line_clip
    
    def create_single_particle(self, particle_id, duration: float):
        """Cria uma partícula individual"""
        # Define área de movimento (apenas na área do vídeo)
        header_height = int(self.height * 0.15)
        footer_height = int(self.height * 0.10)
        video_area_height = self.height - header_height - footer_height
        
        # Posição inicial aleatória dentro da área do vídeo
        x = random.randint(10, self.width - 10)
        y = random.randint(header_height + 10, header_height + video_area_height - 10)
        
        # Velocidade e direção (mais suaves)
        vx = random.uniform(-15, 15)
        vy = random.uniform(-10, 10)
        
        # Tamanho
        size = random.randint(2, 4)
        
        # Cor
        colors = [(100, 150, 255), (200, 100, 255), (255, 100, 200)]
        color = random.choice(colors)
        
        def make_particle_frame(t):
            # Calcula nova posição
            new_x = int(x + vx * t)
            new_y = int(y + vy * t)
            
            # Mantém dentro dos limites da área do vídeo
            new_x = max(size//2, min(self.width - size//2, new_x))
            new_y = max(header_height + size//2, 
                       min(header_height + video_area_height - size//2, new_y))
            
            # Cria frame da partícula
            frame = np.zeros((size, size, 3), dtype=np.uint8)
            frame[:, :] = color
            
            # Adiciona transparência baseada no tempo
            opacity = 0.6 + 0.4 * math.sin(t * 2 + particle_id)
            frame = (frame * opacity).astype(np.uint8)
            
            return frame
        
        particle_clip = VideoClip(make_particle_frame, duration=duration)
        particle_clip = particle_clip.set_position((x, y))
        
        return particle_clip
    
    def generate_tts_audio(self, script: str) -> str:
        """Gera áudio TTS otimizado para velocidade"""
        try:
            response = openai.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=script,
                speed=1.5  # Aumenta velocidade em 20%
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
        """Cria um outro completo e melhorado"""
        print(f"Gerando outro {outro_number} melhorado...")
        
        # Seleciona script TTS
        tts_script = self.tts_scripts[outro_number - 1]
        
        # Gera áudio TTS
        print("Gerando áudio TTS otimizado...")
        audio_path = self.generate_tts_audio(tts_script)
        
        if not audio_path:
            print("Erro: Não foi possível gerar áudio TTS")
            return None
        
        # Carrega o áudio TTS
        audio_clip = mp.AudioFileClip(audio_path)
        
        # Ajusta duração do vídeo para o áudio
        video_duration = audio_clip.duration
        print(f"Duração do TTS: {video_duration:.2f}s")
        
        # Cria elementos visuais com duração correta
        background = self.create_animated_background(video_duration)
        header_elements = self.create_animated_header(video_duration)
        footer_elements = self.create_animated_footer(video_duration)
        particle_effects = self.create_particle_effects(video_duration)
        
        # Logo animado (se disponível)
        logo_element = self.create_animated_logo(video_duration)
        if logo_element:
            all_elements = [background, logo_element] + header_elements + footer_elements + particle_effects
        else:
            all_elements = [background] + header_elements + footer_elements + particle_effects
        
        # Combina todos os elementos
        video_clip = CompositeVideoClip(all_elements, size=(self.width, self.height))
        
        # Adiciona áudio TTS
        final_clip = video_clip.set_audio(audio_clip)
        
        # Salva o outro
        output_path = self.assets_dir / f"outro{outro_number}.mp4"
        
        print(f"Renderizando outro {outro_number} melhorado...")
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
        
        # Remove arquivo temporário TTS
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
        except PermissionError:
            print(f"⚠️  Não foi possível remover arquivo TTS: {audio_path}")
        except Exception as e:
            print(f"⚠️  Erro ao remover arquivo TTS: {e}")
        
        print(f"✅ Outro {outro_number} melhorado gerado: {output_path}")
        return output_path
    
    def generate_all_outros(self):
        """Gera todos os 3 outros melhorados"""
        print("🎬 Iniciando geração dos outros melhorados do ClipVerso...")
        
        generated_outros = []
        
        for i in range(1, 4):
            outro_path = self.create_outro(i)
            if outro_path:
                generated_outros.append(outro_path)
        
        print(f"\n🎉 Geração concluída! {len(generated_outros)} outros melhorados criados:")
        for path in generated_outros:
            print(f"  - {path}")
        
        return generated_outros

def main():
    """Função principal"""
    generator = EnhancedOutroGenerator()
    generator.generate_all_outros()

if __name__ == "__main__":
    main() 