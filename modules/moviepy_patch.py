import cv2
import numpy as np
import moviepy.video.fx.resize as resize
import warnings
import atexit

# Patch para usar OpenCV como resizer
def patch_resize():
    def new_resizer(pic, newsize):
        lx, ly = int(newsize[0]), int(newsize[1])
        if lx > pic.shape[1] or ly > pic.shape[0]:
            # Para aumentar o tamanho, usa INTER_LINEAR para boa qualidade e velocidade
            interpolation = cv2.INTER_LINEAR
        else:
            # Para diminuir o tamanho, usa INTER_AREA para evitar aliasing
            interpolation = cv2.INTER_AREA
        return cv2.resize(pic.astype('uint8'), (lx, ly),
                         interpolation=interpolation)
    
    resize.resizer = new_resizer
    resize.resizer.origin = "cv2"

# Patch para melhorar gerenciamento de recursos do MoviePy
def patch_moviepy_resources():
    """Aplica patches para melhorar gerenciamento de recursos"""
    
    # Suprime warnings do MoviePy
    warnings.filterwarnings("ignore", category=ResourceWarning)
    warnings.filterwarnings("ignore", category=UserWarning, module="moviepy")
    
    # Patch para melhorar limpeza de recursos
    import moviepy.audio.io.readers as readers
    
    original_del = readers.FFMPEG_AudioReader.__del__
    
    def safe_del(self):
        try:
            if hasattr(self, 'proc') and self.proc:
                try:
                    self.close_proc()
                except (OSError, AttributeError):
                    pass
        except Exception:
            pass
    
    readers.FFMPEG_AudioReader.__del__ = safe_del
    
    # Registra função de limpeza ao sair
    def cleanup_moviepy():
        try:
            import moviepy.editor as mp
            # Força limpeza de recursos
            mp.close_all_clips()
        except:
            pass
    
    atexit.register(cleanup_moviepy)

# Aplica todos os patches
def apply_all_patches():
    """Aplica todos os patches do MoviePy"""
    patch_resize()
    patch_moviepy_resources()
    print("✅ Patches do MoviePy aplicados") 