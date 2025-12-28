
import pygame
from test9.utils.config import own_ship
from test9.components.get_color import get_color
from test9.main import screen

def draw_own_ship_data(panel):
    """Draw own ship data panel"""
    if panel.collapsed:
        panel.draw(screen)
        return
        
    font_data = pygame.font.SysFont("Courier New", 11, bold=True)
    panel.draw(screen)
    
    y = panel.rect.y + 35
    
    data = [
        ("HEADING:", f"{own_ship['heading']}°"),
        ("SPEED:", f"{own_ship['speed']} kts"),
        ("COURSE:", f"{own_ship['course']}°"),
        ("POSITION:", own_ship['lat']),
        ("", own_ship['lon']),
        ("DEPTH:", f"{own_ship['depth']} m")
    ]
    
    for label, value in data:
        label_surf = font_data.render(label, True, get_color("primary"))
        value_surf = font_data.render(value, True, get_color("accent"))
        screen.blit(label_surf, (panel.rect.x + 10, y))
        screen.blit(value_surf, (panel.rect.x + 120, y))
        y += 22
