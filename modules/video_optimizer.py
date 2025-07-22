# modules/video_optimizer.py
"""
Módulo para otimizações de processamento de vídeo
Inclui suporte para GPU AMD e outras otimizações
"""
import os
import subprocess
import platform
from pathlib import Path

def detect_amd_gpu():
    """
    Detecta se há uma GPU AMD disponível
    """
    try:
        # Windows - verifica via PowerShell
        if platform.system() == "Windows":
            result = subprocess.run(
                ["powershell", "Get-WmiObject -Class Win32_VideoController | Where-Object {$_.Name -like '*AMD*' -or $_.Name -like '*Radeon*'} | Select-Object Name"],
                capture_output=True, text=True, timeout=10
            )
            if "AMD" in result.stdout or "Radeon" in result.stdout:
                return True
        
        # Linux - verifica via lspci
        elif platform.system() == "Linux":
            result = subprocess.run(
                ["lspci", "-v"], capture_output=True, text=True, timeout=10
            )
            if "AMD" in result.stdout or "Radeon" in result.stdout:
                return True
        
        # macOS - verifica via system_profiler
        elif platform.system() == "Darwin":
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType"], capture_output=True, text=True, timeout=10
            )
            if "AMD" in result.stdout or "Radeon" in result.stdout:
                return True
                
    except Exception as e:
        print(f"Erro ao detectar GPU AMD: {e}")
    
    return False

def get_optimal_ffmpeg_params(use_gpu=True, quality="balanced"):
    """
    Retorna parâmetros otimizados do FFmpeg baseado na configuração
    """
    base_params = [
        "-profile:v", "main",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",  # Otimiza para streaming
        "-g", "30",  # GOP size otimizado para 30fps
    ]
    
    if use_gpu and detect_amd_gpu():
        # Parâmetros para GPU AMD (AMF - AMD Media Framework)
        gpu_params = [
            "-c:v", "h264_amf",  # Codec AMD
            "-quality", "speed",  # Prioriza velocidade
            "-rc", "vbr_peak",  # Rate control otimizado
            "-b:v", "5M",  # Bitrate base
            "-maxrate", "10M",  # Bitrate máximo
            "-bufsize", "10M",  # Buffer size
            "-profile:v", "main",  # Perfil de codificação
        ]
        
        if quality == "high":
            gpu_params.extend(["-b:v", "8M", "-maxrate", "15M"])
        elif quality == "fast":
            gpu_params.extend(["-b:v", "3M", "-maxrate", "6M"])
            
        return gpu_params  # Retorna apenas parâmetros AMD, sem base_params
    
    else:
        # Parâmetros otimizados para CPU
        cpu_params = [
            "-c:v", "libx264",
            "-preset", "faster",  # Mais rápido que 'fast'
            "-crf", "23",  # Qualidade constante
            "-tune", "fastdecode",  # Otimizado para decodificação rápida
        ]
        
        if quality == "high":
            cpu_params.extend(["-preset", "fast", "-crf", "20"])
        elif quality == "fast":
            cpu_params.extend(["-preset", "ultrafast", "-crf", "28"])
            
        return base_params + cpu_params

def get_optimal_audio_params():
    """
    Retorna parâmetros otimizados para áudio
    """
    return [
        "-c:a", "aac",
        "-b:a", "128k",  # Bitrate de áudio otimizado
        "-ar", "44100",  # Sample rate padrão
        "-ac", "2",  # Estéreo
    ]

def optimize_video_processing_settings():
    """
    Configurações otimizadas para processamento de vídeo
    """
    settings = {
        "use_gpu": detect_amd_gpu(),
        "quality": "balanced",  # balanced, fast, high
        "threads": os.cpu_count(),
        "memory_limit": "2G",  # Limite de memória para FFmpeg
    }
    
    # Ajusta threads baseado no sistema
    if settings["threads"] > 8:
        settings["threads"] = 8  # Limita para evitar sobrecarga
    
    return settings

def get_ffmpeg_threads_param():
    """
    Retorna parâmetro de threads otimizado para FFmpeg
    """
    threads = os.cpu_count()
    if threads > 8:
        threads = 8
    return ["-threads", str(threads)]

def create_optimized_write_params(use_gpu=True, quality="balanced"):
    """
    Cria parâmetros otimizados para write_videofile
    """
    settings = optimize_video_processing_settings()
    
    # Parâmetros base
    params = {
        "codec": "h264_amf" if (use_gpu and settings["use_gpu"]) else "libx264",
        "fps": 30,
        "audio_codec": "aac",
        "ffmpeg_params": get_optimal_ffmpeg_params(use_gpu, quality) + get_optimal_audio_params() + get_ffmpeg_threads_param(),
    }
    
    # Ajusta preset apenas para libx264 (AMD não usa preset)
    if params["codec"] == "libx264":
        if quality == "fast":
            params["preset"] = "ultrafast"
        elif quality == "high":
            params["preset"] = "fast"
        else:
            params["preset"] = "faster"
    
    return params

def print_optimization_info():
    """
    Imprime informações sobre as otimizações aplicadas
    """
    settings = optimize_video_processing_settings()
    
    print("🚀 Configurações de Otimização:")
    print(f"   GPU AMD detectada: {'✅ Sim' if settings['use_gpu'] else '❌ Não'}")
    print(f"   Qualidade: {settings['quality']}")
    print(f"   Threads: {settings['threads']}")
    print(f"   Codec: {'h264_amf (GPU)' if settings['use_gpu'] else 'libx264 (CPU)'}")
    
    if settings['use_gpu']:
        print("   ⚡ Usando aceleração por GPU AMD")
    else:
        print("   💻 Usando processamento por CPU otimizado")

def create_fallback_params():
    """
    Cria parâmetros de fallback para quando o codec AMD falha
    """
    return {
        "codec": "libx264",
        "fps": 30,
        "preset": "ultrafast",
        "audio_codec": "aac",
        "ffmpeg_params": [
            "-profile:v", "main",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-crf", "28",
            "-c:a", "aac",
            "-b:a", "128k",
            "-ar", "44100",
            "-ac", "2",
        ] + get_ffmpeg_threads_param()
    } 