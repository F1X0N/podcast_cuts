import os
import subprocess

# Configura o caminho do ImageMagick usando variável de ambiente
def setup_imagemagick():
    """Configura o ImageMagick para o MoviePy"""
    # Prioriza o caminho completo que sabemos que funciona
    primary_path = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
    
    if os.path.exists(primary_path):
        os.environ["IMAGEMAGICK_BINARY"] = primary_path
        print(f"✅ ImageMagick encontrado: {primary_path}")
        return True
    
    # Fallback para outros caminhos possíveis
    possible_paths = [
        r"C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe",
        r"C:\Program Files\ImageMagick-7.1.1\magick.exe",
        "magick"  # Se estiver no PATH
    ]
    
    # Verifica qual caminho existe
    for path in possible_paths:
        if path == "magick":
            # Testa se o comando magick está disponível
            try:
                subprocess.run([path, "--version"], capture_output=True, check=True)
                os.environ["IMAGEMAGICK_BINARY"] = path
                print(f"✅ ImageMagick encontrado: {path}")
                return True
            except:
                continue
        elif os.path.exists(path):
            os.environ["IMAGEMAGICK_BINARY"] = path
            print(f"✅ ImageMagick encontrado: {path}")
            return True
    
    print("⚠️ ImageMagick não encontrado. TextClips podem não funcionar corretamente.")
    return False

# Executa a configuração
setup_imagemagick() 