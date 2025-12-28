
import pygame
from test9.components.get_color import get_color
from test9.main import screen, target_manager
from test9.classes.mode_config import ModeConfig


def draw_tracked_targets(panel):
    """Draw tracked targets panel"""
    if panel.collapsed:
        panel.draw(screen)
        return
        
    font_header = pygame.font.SysFont("Courier New", 10, bold=True)
    font_data = pygame.font.SysFont("Courier New", 9, bold=True)
    
    panel.draw(screen)
    
    y = panel.rect.y + 30
    
    # Headers
    headers = ["ID", "RNG", "BRG", "VEL", "THR"]
    header_x = [10, 60, 110, 180, 250]
    
    for i, header in enumerate(headers):
        header_surf = font_header.render(header, True, get_color("primary"))
        screen.blit(header_surf, (panel.rect.x + header_x[i], y))
    
    y += 18
    pygame.draw.line(screen, get_color("primary"), 
                    (panel.rect.x + 10, y), 
                    (panel.rect.x + panel.rect.width - 10, y), 1)
    y += 8
    
    # Target data
    sorted_targets = sorted(target_manager.targets.values(), key=lambda t: t.distance)
    
    for target in sorted_targets[:20]:
        color = target.get_color()
        
        data = [
            f"T{target.id}",
            f"{target.get_range_nm():.1f}",
            f"{int(target.angle)}°",
            f"{int(target.velocity)}",
            target.threat_level[:3]
        ]
        
        for i, text in enumerate(data):
            text_surf = font_data.render(text, True, color)
            screen.blit(text_surf, (panel.rect.x + header_x[i], y))
        
        y += 16
        if y > panel.rect.y + panel.rect.height - 20:
            break
