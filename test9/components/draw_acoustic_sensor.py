import pygame
import numpy as np
import sounddevice as sd
import math
from collections import deque
from test9.main import screen
from test9.components.get_color import get_color
from test9.utils.config import current_noise_data


def draw_acoustic_sensor(panel):
    """Draw acoustic sensor panel"""
    if panel.collapsed:
        panel.draw(screen)
        return
        
    font_data = pygame.font.SysFont("Courier New", 11, bold=True)
    panel.draw(screen)
    
    y = panel.rect.y + 30
    
    # Signal strength bar
    bar_width = int(current_noise_data["intensity"] * 250)
    bar_color = get_color("primary") if current_noise_data["intensity"] < 0.7 else get_color("danger")
    pygame.draw.rect(screen, bar_color, (panel.rect.x + 10, y, bar_width, 15))
    pygame.draw.rect(screen, get_color("primary"), (panel.rect.x + 10, y, 250, 15), 1)
    
    signal_text = font_data.render(f"{current_noise_data['intensity']:.2f}", True, get_color("accent"))
    screen.blit(signal_text, (panel.rect.x + 265, y))
    
    y += 25
    
    # Frequency and bearing
    info = [
        ("FREQ:", f"{int(current_noise_data['dominant_freq'])} Hz"),
        ("BEARING:", f"{math.degrees(current_noise_data['angle']):.1f}°"),
        ("CONF:", f"{current_noise_data['confidence']:.0f}%")
    ]
    
    for label, value in info:
        label_surf = font_data.render(label, True, get_color("primary"))
        value_surf = font_data.render(value, True, get_color("accent"))
        screen.blit(label_surf, (panel.rect.x + 10, y))
        screen.blit(value_surf, (panel.rect.x + 150, y))
        y += 20
