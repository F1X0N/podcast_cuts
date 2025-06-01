import os
from moviepy.config import change_settings

# Configura o caminho do ImageMagick
# Você pode precisar ajustar este caminho dependendo de onde o ImageMagick foi instalado
IMAGEMAGICK_BINARY = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"

# Aplica a configuração
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_BINARY}) 