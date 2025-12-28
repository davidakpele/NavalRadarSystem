

import pygame
from test9.main import target_manager
from test9.utils.config import RADAR_RADIUS

# ============================================================================
# SONAR PULSE SYSTEM
# ============================================================================
def send_sonar_pulse():
    """Send active sonar pulse"""
    global sonar_pulse_time, sonar_echo_targets
    
    sonar_pulse_time = pygame.time.get_ticks()
    sonar_echo_targets = []
    
    # Simulate echo returns
    for target in target_manager.targets.values():
        # Calculate echo delay based on distance
        echo_delay = (target.distance / RADAR_RADIUS) * 1000  # milliseconds
        echo_strength = target.intensity * 0.8  # Echo attenuation
        
        sonar_echo_targets.append({
            'target': target,
            'echo_time': sonar_pulse_time + echo_delay,
            'echo_strength': echo_strength,
            'displayed': False
        })
    
    print(f"[SONAR] Pulse sent. Expecting {len(sonar_echo_targets)} echoes")
