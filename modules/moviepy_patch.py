import cv2
import numpy as np
import moviepy.video.fx.resize as resize

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