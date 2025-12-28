import math
import pygame
from test9.utils.config import RADAR_RADIUS, RADAR_CENTER
from test9.components.get_color import get_color
from test9.main import brightness, zoom_level, screen 


def draw_compass():
    """Draw compass rose"""
    font = pygame.font.SysFont("Courier New", 14, bold=True)
    primary_color = tuple(int(c * brightness) for c in get_color("primary"))
    
    directions = [
        (0, "N"), (45, "NE"), (90, "E"), (135, "SE"),
        (180, "S"), (225, "SW"), (270, "W"), (315, "NW")
    ]
    
    for angle, label in directions:
        offset = (RADAR_RADIUS + 30) * zoom_level
        x = RADAR_CENTER[0] + offset * math.cos(math.radians(angle - 90))
        y = RADAR_CENTER[1] + offset * math.sin(math.radians(angle - 90))
        
        text = font.render(label, True, primary_color)
        text_rect = text.get_rect(center=(x, y))
        screen.blit(text, text_rect)
