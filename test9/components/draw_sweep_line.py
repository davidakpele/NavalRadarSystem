import math
import pygame
from test9.utils.config import RADAR_RADIUS, RADAR_CENTER
from test9.components.get_color import get_color
from test9.main import brightness, zoom_level, screen, sweep_angle, current_mode, narrow_beam_angle
from test9.classes.mode_config import ModeConfig
from test9.classes.detection_mode import DetectionMode

def draw_sweep_line():
    """Draw the radar sweep line"""
    config = ModeConfig.get_config(current_mode)
    
    if current_mode == DetectionMode.OMNI_360:
        # Draw pulsing circle for omni mode
        pulse_alpha = int(128 + 127 * math.sin(pygame.time.get_ticks() / 200))
        color = (*config["color"], pulse_alpha)
        pygame.draw.circle(screen, color, RADAR_CENTER, int(RADAR_RADIUS * zoom_level), 2)
        
    elif current_mode == DetectionMode.NARROW_BEAM:
        # Draw focused beam
        angle = narrow_beam_angle
        arc_width = config["detection_arc"]
        
        # Draw beam cone
        for i in range(-int(arc_width/2), int(arc_width/2), 2):
            beam_angle = angle + i
            end_x = RADAR_CENTER[0] + (RADAR_RADIUS * zoom_level) * math.cos(math.radians(beam_angle - 90))
            end_y = RADAR_CENTER[1] + (RADAR_RADIUS * zoom_level) * math.sin(math.radians(beam_angle - 90))
            
            alpha = int(255 * (1 - abs(i) / (arc_width/2)))
            color = (*config["color"][:3], alpha)
            pygame.draw.line(screen, color, RADAR_CENTER, (end_x, end_y), 2)
            
    elif current_mode == DetectionMode.WIDE_BEAM:
        # Draw wide beam
        arc_width = config["detection_arc"]
        
        for i in range(-int(arc_width/2), int(arc_width/2), 3):
            beam_angle = sweep_angle + i
            end_x = RADAR_CENTER[0] + (RADAR_RADIUS * zoom_level) * math.cos(math.radians(beam_angle - 90))
            end_y = RADAR_CENTER[1] + (RADAR_RADIUS * zoom_level) * math.sin(math.radians(beam_angle - 90))
            
            alpha = int(128 * (1 - abs(i) / (arc_width/2)))
            color = (*config["color"][:3], alpha)
            pygame.draw.line(screen, color, RADAR_CENTER, (end_x, end_y), 2)
    
    else:
        # Standard sweep line
        end_x = RADAR_CENTER[0] + (RADAR_RADIUS * zoom_level) * math.cos(math.radians(sweep_angle - 90))
        end_y = RADAR_CENTER[1] + (RADAR_RADIUS * zoom_level) * math.sin(math.radians(sweep_angle - 90))
        pygame.draw.line(screen, config["color"], RADAR_CENTER, (end_x, end_y), 2)
        
        # Draw fade trail
        for i in range(1, 20):
            trail_angle = sweep_angle - i * 2
            trail_alpha = int(255 * (1 - i / 20))
            trail_end_x = RADAR_CENTER[0] + (RADAR_RADIUS * zoom_level) * math.cos(math.radians(trail_angle - 90))
            trail_end_y = RADAR_CENTER[1] + (RADAR_RADIUS * zoom_level) * math.sin(math.radians(trail_angle - 90))
            
            color = (*config["color"][:3], trail_alpha)
            pygame.draw.line(screen, color, RADAR_CENTER, (trail_end_x, trail_end_y), 1)
