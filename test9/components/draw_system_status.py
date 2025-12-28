
import pygame
from test9.utils.config import clock, paused
from test9.components.get_color import get_color
from test9.main import current_mode, screen, range_setting, frequency_filter, target_manager, gain_control, current_theme_name, recorder
from test9.classes.mode_config import ModeConfig


def draw_system_status(panel):
    """Draw system status panel"""
    if panel.collapsed:
        panel.draw(screen)
        return
        
    font_data = pygame.font.SysFont("Courier New", 11, bold=True)
    panel.draw(screen)
    
    y = panel.rect.y + 35
    
    data = [
        ("STATUS:", "OPERATIONAL" if not paused else "PAUSED"),
        ("MODE:", ModeConfig.get_config(current_mode)["name"]),
        ("TARGETS:", str(len(target_manager.targets))),
        ("RANGE:", f"{range_setting} NM"),
        ("GAIN:", f"{gain_control:.1f}x"),
        ("FILTER:", frequency_filter if frequency_filter else "NONE"),
        ("THEME:", current_theme_name.upper()),
        ("RECORDING:", "ACTIVE" if recorder.recording else "STANDBY"),
        ("FPS:", str(int(clock.get_fps())))
    ]
    
    for label, value in data:
        label_surf = font_data.render(label, True, get_color("primary"))
        value_surf = font_data.render(value, True, get_color("accent"))
        screen.blit(label_surf, (panel.rect.x + 10, y))
        screen.blit(value_surf, (panel.rect.x + 150, y))
        y += 22
