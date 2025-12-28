
import pygame
from test9.utils.config import WIDTH, HEIGHT
from test9.components.get_color import get_color
from test9.main import screen

def draw_crt_effect():
    """Draw CRT screen effect"""
    # Scanlines
    for y in range(0, HEIGHT, 3):
        pygame.draw.line(screen, (0, 0, 0, 50), (0, y), (WIDTH, y), 1)
    
    # Screen curvature (simulated with vignette)
    vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(vignette, (0, 0, 0, 100), (WIDTH//2, HEIGHT//2), 
                      int(min(WIDTH, HEIGHT) * 0.6))
    pygame.draw.circle(vignette, (0, 0, 0, 0), (WIDTH//2, HEIGHT//2), 
                      int(min(WIDTH, HEIGHT) * 0.4))
    screen.blit(vignette, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
