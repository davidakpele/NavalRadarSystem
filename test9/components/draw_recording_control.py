import time
import pygame
from test9.utils.config import screen
from test9.main import recorder
from test9.components.get_color import get_color

def draw_recording_control(panel):
    """Draw recording control panel"""
    if panel.collapsed:
        panel.draw(screen)
        return
        
    font_data = pygame.font.SysFont("Courier New", 10, bold=True)
    panel.draw(screen)
    
    y = panel.rect.y + 35
    
    # Recording status
    status = "RECORDING" if recorder.recording else "READY"
    status_color = get_color("danger") if recorder.recording else get_color("primary")
    status_text = font_data.render(f"STATUS: {status}", True, status_color)
    screen.blit(status_text, (panel.rect.x + 10, y))
    y += 25
    
    # Recording info
    if recorder.recording and recorder.session_data:
        duration = time.time() - recorder.session_data.start_time
        duration_text = font_data.render(f"DURATION: {int(duration)}s", True, get_color("accent"))
        screen.blit(duration_text, (panel.rect.x + 10, y))
        y += 20
        
        frames_text = font_data.render(f"FRAMES: {len(recorder.frame_buffer)}", True, get_color("accent"))
        screen.blit(frames_text, (panel.rect.x + 10, y))
        y += 20
        
        targets_text = font_data.render(f"EVENTS: {len(recorder.session_data.target_history)}", True, get_color("accent"))
        screen.blit(targets_text, (panel.rect.x + 10, y))
        y += 25
    
    # Controls
    controls = [
        "[R] Start/Stop Recording",
        "[S] Screenshot",
        "[E] Export Target CSV",
        "[J] Export All JSON",
        "[C] Clear All Targets"
    ]
    
    for control in controls:
        text = font_data.render(control, True, get_color("primary"))
        screen.blit(text, (panel.rect.x + 10, y))
        y += 18
