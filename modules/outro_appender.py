# modules/outro_appender.py
"""
Módulo para anexar outros aos cortes do ClipVerso
"""

import random
import os
from pathlib import Path
import moviepy.editor as mp
from .video_optimizer import create_optimized_write_params, create_fallback_params

class OutroAppender:
    def __init__(self, assets_dir: str = "assets/outros"):
        self.assets_dir = Path(assets_dir)
        self.outro_files = []
        self._load_outros()
    
    def _load_outros(self):
        """Carrega os arquivos de outros disponíveis"""
        if not self.assets_dir.exists():
            print(f"⚠️  Diretório de outros não encontrado: {self.assets_dir}")
            return
        
        # Procura por arquivos outro1.mp4, outro2.mp4, outro3.mp4
        for i in range(1, 4):
            outro_path = self.assets_dir / f"outro{i}.mp4"
            if outro_path.exists():
                self.outro_files.append(str(outro_path))
        
        if not self.outro_files:
            print(f"⚠️  Nenhum arquivo de outro encontrado em {self.assets_dir}")
            print("   Execute 'python generate_outros.py' para gerar os outros")
        else:
            print(f"✅ {len(self.outro_files)} outros carregados")
    
    def get_random_outro(self) -> str:
        """Retorna o caminho de um outro aleatório"""
        if not self.outro_files:
            raise FileNotFoundError("Nenhum arquivo de outro disponível")
        
        return random.choice(self.outro_files)
    
    def append_outro(self, input_clip_path: str, optimization_config: dict = None) -> str:
        """
        Anexa um outro aleatório ao final do corte
        
        Args:
            input_clip_path: Caminho do arquivo de vídeo de entrada
            optimization_config: Configurações de otimização de vídeo
        
        Returns:
            str: Caminho do arquivo de vídeo com outro anexado
        """
        if not self.outro_files:
            raise FileNotFoundError("Nenhum arquivo de outro disponível. Execute 'python generate_outros.py' primeiro.")
        
        # Configurações de otimização padrão
        if optimization_config is None:
            optimization_config = {
                "use_gpu": True,
                "quality": "balanced",
                "enable_parallel": True
            }
        
        input_path = Path(input_clip_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Arquivo de entrada não encontrado: {input_clip_path}")
        
        # Seleciona um outro aleatório
        outro_path = self.get_random_outro()
        outro_name = Path(outro_path).stem
        
        print(f"🎬 Anexando outro: {outro_name}")
        
        try:
            # Carrega o vídeo principal
            main_clip = mp.VideoFileClip(str(input_path))
            
            # Carrega o outro
            outro_clip = mp.VideoFileClip(outro_path)
            
            # Cria transição de 1 segundo entre o corte e o outro
            transition_duration = 1.0
            
            # Cria um fade out no final do vídeo principal (visual e áudio)
            main_clip = main_clip.fadeout(transition_duration)
            
            # Cria um fade out no áudio do corte principal
            if main_clip.audio:
                main_clip = main_clip.set_audio(main_clip.audio.audio_fadeout(transition_duration))
            
            # Cria um fade in no início do outro (visual e áudio)
            outro_clip = outro_clip.fadein(transition_duration)
            
            # Mantém o áudio do outro em volume total (sem fade in)
            # O TTS deve manter o mesmo volume do áudio do vídeo
            
            # Concatena os vídeos com transição
            final_clip = mp.concatenate_videoclips([main_clip, outro_clip])
            
            # Adiciona música de fundo com controle de volume dinâmico
            background_music_path = Path("assets/fundo.mp3")
            if background_music_path.exists():
                print("🎵 Adicionando música de fundo com controle de volume...")
                
                # Carrega a música de fundo
                background_music = mp.AudioFileClip(str(background_music_path))
                
                # Seleciona um trecho aleatório da música
                music_duration = final_clip.duration
                if background_music.duration > music_duration:
                    # Escolhe um ponto de início aleatório
                    max_start = background_music.duration - music_duration
                    start_time = random.uniform(0, max_start)
                    background_music = background_music.subclip(start_time, start_time + music_duration)
                else:
                    # Se a música for menor, repete até cobrir a duração
                    repeats_needed = int(music_duration / background_music.duration) + 1
                    background_music = mp.concatenate_audioclips([background_music] * repeats_needed)
                    background_music = background_music.subclip(0, music_duration)
                
                # Aplica controle de volume simplificado
                # Reduz volume da música para não competir com o áudio principal
                background_music = background_music.volumex(0.06)  # 6% do volume
                
                # Combina com o áudio original
                final_audio = mp.CompositeAudioClip([final_clip.audio, background_music])
                final_clip = final_clip.set_audio(final_audio)
                
                print("✅ Música de fundo adicionada com controle de volume dinâmico")
            else:
                print("⚠️ Arquivo de música de fundo não encontrado: assets/fundo.mp3")
            
            # Gera nome do arquivo de saída
            output_path = input_path.parent / f"{input_path.stem}_com_outro.mp4"
            
            # Usa parâmetros otimizados
            write_params = create_optimized_write_params(
                use_gpu=optimization_config["use_gpu"],
                quality=optimization_config["quality"]
            )
            
            print(f"🎬 Renderizando vídeo com outro...")
            print(f"   Duração original: {main_clip.duration:.1f}s")
            print(f"   Duração do outro: {outro_clip.duration:.1f}s")
            print(f"   Duração final: {final_clip.duration:.1f}s")
            
            try:
                final_clip.write_videofile(str(output_path), **write_params)
            except Exception as e:
                if "h264_amf" in str(write_params.get('codec', '')) and "Invalid argument" in str(e):
                    print("⚠️ Erro no codec AMD, usando fallback para CPU...")
                    fallback_params = create_fallback_params()
                    print(f"🔄 Renderizando com fallback: {fallback_params['codec']}")
                    final_clip.write_videofile(str(output_path), **fallback_params)
                else:
                    raise e
            
            # Limpa recursos
            main_clip.close()
            outro_clip.close()
            final_clip.close()
            
            print(f"✅ Outro anexado com sucesso: {output_path}")
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Erro ao anexar outro: {e}")
            raise e
    
    def list_available_outros(self):
        """Lista os outros disponíveis"""
        if not self.outro_files:
            print("Nenhum outro disponível")
            return
        
        print("Outros disponíveis:")
        for i, outro_path in enumerate(self.outro_files, 1):
            outro_name = Path(outro_path).name
            print(f"  {i}. {outro_name}")
    
    def validate_outros(self) -> bool:
        """Valida se os outros estão prontos para uso"""
        if not self.outro_files:
            print("❌ Nenhum outro encontrado")
            return False
        
        # Verifica se todos os arquivos existem e são válidos
        for outro_path in self.outro_files:
            if not Path(outro_path).exists():
                print(f"❌ Arquivo não encontrado: {outro_path}")
                return False
            
            try:
                # Tenta carregar o vídeo para validar
                clip = mp.VideoFileClip(outro_path)
                clip.close()
            except Exception as e:
                print(f"❌ Arquivo inválido {outro_path}: {e}")
                return False
        
        print(f"✅ {len(self.outro_files)} outros válidos encontrados")
        return True

def append_outro(input_clip: str, optimization_config: dict = None) -> str:
    """
    Função helper para anexar outro a um corte
    
    Args:
        input_clip: Caminho do arquivo de vídeo
        optimization_config: Configurações de otimização
    
    Returns:
        str: Caminho do arquivo com outro anexado
    """
    appender = OutroAppender()
    return appender.append_outro(input_clip, optimization_config) 