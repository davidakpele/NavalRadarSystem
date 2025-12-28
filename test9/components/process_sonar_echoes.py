

import pygame
from test9.main import sound_system
from test9.classes.mode_config import ModeConfig
from test9.classes.detection_mode import DetectionMode
from test9.utils.config import sonar_echo_targets

def process_sonar_echoes():
    """Process and display sonar echoes"""
    current_time = pygame.time.get_ticks()
    
    for echo in sonar_echo_targets:
        if not echo['displayed'] and current_time >= echo['echo_time']:
            # Display echo
            echo['displayed'] = True
            target = echo['target']
            
            # Play echo sound
            sound_system.play_sonar_echo(echo['echo_strength'])  # NEW
            
            # Update target with accurate range
            config = ModeConfig.get_config(DetectionMode.ACTIVE_SONAR)
            actual_distance = target.distance * config['range_multiplier']
            target.update(target.angle, actual_distance, echo['echo_strength'])
