import pygame
from components.get_color import get_color
from test9.main import current_mode, screen
from test9.classes.mode_config import ModeConfig
from test9.classes.detection_mode import DetectionMode

def draw_mode_selector(panel):
    """Draw detection mode selector"""
    if panel.collapsed:
        panel.draw(screen)
        return
    
    font_data = pygame.font.SysFont("Courier New", 11, bold=True)
    panel.draw(screen)
    
    y = panel.rect.y + 35
    modes = [
        DetectionMode.PASSIVE,
        DetectionMode.ACTIVE_SONAR,
        DetectionMode.WIDE_BEAM,
        DetectionMode.NARROW_BEAM,
        DetectionMode.OMNI_360
    ]
    
    for i, mode in enumerate(modes):
        config = ModeConfig.get_config(mode)
        is_active = (mode == current_mode)
        
        # Mode indicator
        indicator_color = config["color"] if is_active else get_color("secondary")
        pygame.draw.circle(screen, indicator_color, (panel.rect.x + 20, y + 7), 6)
        
        # Mode name
        mode_text = f"[{i+1}] {config['name']}"
        text_color = get_color("accent") if is_active else get_color("primary")
        text = font_data.render(mode_text, True, text_color)
        screen.blit(text, (panel.rect.x + 35, y))
        
        # Description
        desc_text = f"    {config['description']}"
        desc = font_data.render(desc_text, True, get_color("primary"))
        screen.blit(desc, (panel.rect.x + 35, y + 15))
        
        y += 35
