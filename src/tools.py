import io
import cairosvg
import pygame
from PIL import Image

def loadSvgSprite(svgPath):
    pngBytes = cairosvg.svg2png(url=svgPath)
    imageStream = io.BytesIO(pngBytes)
    pillowImage = Image.open(imageStream).convert("RGBA")
    mode, size, data = pillowImage.mode, pillowImage.size, pillowImage.tobytes()
    return pygame.image.frombuffer(data, size, mode)