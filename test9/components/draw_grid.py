import math

import pygame
from test9.utils.config import RADAR_CENTER, RADAR_RADIUS
from test9.components.get_color import get_color
from test9.main import brightness, zoom_level, screen

def draw_grid():
    """Draw radar grid"""
    primary_color = tuple(int(c * brightness * 0.5) for c in get_color("primary"))
    
    # Radial lines every 30 degrees
    for angle in range(0, 360, 30):
        end_x = RADAR_CENTER[0] + (RADAR_RADIUS * zoom_level) * math.cos(math.radians(angle - 90))
        end_y = RADAR_CENTER[1] + (RADAR_RADIUS * zoom_level) * math.sin(math.radians(angle - 90))
        pygame.draw.line(screen, primary_color, RADAR_CENTER, (end_x, end_y), 1)
