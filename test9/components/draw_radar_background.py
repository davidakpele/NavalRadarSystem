import pygame
from test9.utils.config import RADAR_RADIUS, RADAR_CENTER
from test9.components.get_color import get_color
from test9.main import brightness, zoom_level, screen, range_setting, show_grid, show_compass, crt_effect
from test9.components.draw_crt_effect import draw_crt_effect
from test9.components.draw_grid import draw_grid
from test9.components.draw_compass import draw_compass


def draw_radar_background():
    """Draw the radar display background"""
    # Fill background
    bg_color = tuple(int(c * brightness) for c in get_color("bg"))
    screen.fill(bg_color)
    
    # Draw CRT effect if enabled
    if crt_effect:
        draw_crt_effect()
    
    # Draw radar circles
    primary_color = tuple(int(c * brightness) for c in get_color("primary"))
    secondary_color = tuple(int(c * brightness * 0.3) for c in get_color("secondary"))
    
    # Range rings
    for i in range(1, 5):
        radius = int((RADAR_RADIUS / 4) * i * zoom_level)
        pygame.draw.circle(screen, secondary_color, RADAR_CENTER, radius, 1)
        
        # Range labels
        if show_grid:
            range_nm = (range_setting / 4) * i
            font = pygame.font.SysFont("Courier New", 10)
            label = font.render(f"{range_nm:.0f}NM", True, primary_color)
            screen.blit(label, (RADAR_CENTER[0] + radius + 5, RADAR_CENTER[1] - 5))
    
    # Main radar circle
    pygame.draw.circle(screen, primary_color, RADAR_CENTER, int(RADAR_RADIUS * zoom_level), 2)
    
    # Draw grid if enabled
    if show_grid:
        draw_grid()
    
    # Draw compass if enabled
    if show_compass:
        draw_compass()
    
    # Center dot
    pygame.draw.circle(screen, primary_color, RADAR_CENTER, 5)
