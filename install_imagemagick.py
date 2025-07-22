import os
import sys
import requests
import subprocess
import shutil
import time

IMAGEMAGICK_URL = "https://download.imagemagick.org/ImageMagick/download/binaries/ImageMagick-7.1.1-32-Q16-HDRI-x64-dll.exe"
IMAGEMAGICK_EXE = "ImageMagick-7.1.1-32-Q16-HDRI-x64-dll.exe"
INSTALL_PATH = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI"
MAGICK_BINARY = os.path.join(INSTALL_PATH, "magick.exe")
CONFIG_FILE = os.path.join("modules", "moviepy_config.py")


def imagemagick_installed():
    return os.path.exists(MAGICK_BINARY)

def download_imagemagick():
    print("Baixando ImageMagick...")
    r = requests.get(IMAGEMAGICK_URL, stream=True)
    with open(IMAGEMAGICK_EXE, "wb") as f:
        shutil.copyfileobj(r.raw, f)
    print("Download concluído.")

def install_imagemagick():
    print("Instalando ImageMagick (pode ser necessário aceitar permissões de administrador)...")
    # /S = silent, /DIR=... define o diretório de instalação
    subprocess.run([IMAGEMAGICK_EXE, "/S", f"/DIR={INSTALL_PATH}"], check=True)
    print("Instalação concluída.")
    time.sleep(3)  # Aguarda arquivos serem copiados

def update_config():
    print(f"Atualizando {CONFIG_FILE} com o novo caminho do magick.exe...")
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        for line in lines:
            if line.strip().startswith("IMAGEMAGICK_BINARY"):
                f.write(f'IMAGEMAGICK_BINARY = r"{MAGICK_BINARY}"\n')
            else:
                f.write(line)
    print("Configuração atualizada!")

def main():
    if imagemagick_installed():
        print(f"ImageMagick já está instalado em: {MAGICK_BINARY}")
        return
    download_imagemagick()
    install_imagemagick()
    if imagemagick_installed():
        update_config()
        print("Tudo pronto! ImageMagick instalado e configurado.")
    else:
        print("Erro: Não foi possível encontrar o magick.exe após a instalação.")

if __name__ == "__main__":
    if sys.platform != "win32":
        print("Este script é apenas para Windows.")
        sys.exit(1)
    main() 