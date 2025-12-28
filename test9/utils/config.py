# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

from collections import deque
import os
import pygame
from test9.classes.detection_mode import DetectionMode
from test9.classes.color_theme import ColorTheme
from test9.classes.draggable_panel import DraggablePanel

WIDTH, HEIGHT = 1600, 900
CENTER = (450, HEIGHT // 2)  
RADAR_RADIUS = 350 
RADAR_CENTER = (450, HEIGHT // 2)  
FPS = 60
FS = 44100 
CHANNELS = 2
CHUNK = 1024 


audio_queue = deque(maxlen=100)
audio_recording_buffer = deque(maxlen=FS * 60)  # 60 seconds buffer

# ============================================================================
# SYSTEM STATE
# ============================================================================

current_mode = DetectionMode.PASSIVE
sweep_angle = 0
narrow_beam_angle = 0  
sonar_pulse_time = 0
sonar_echo_targets = []
paused = False
brightness = 1.0
show_grid = True
show_compass = True
show_minimap = False
fullscreen = False
crt_effect = False
zoom_level = 1.0
range_setting = 50  # Nautical miles
gain_control = 1.0
noise_gate = 0.05  # Much lower threshold for better detection
frequency_filter = None  # None, 'lowpass', 'highpass', 'bandpass'

# Own ship data
own_ship = {
    "heading": 342.5,
    "speed": 18.2,
    "lat": "34° 02.1' N",
    "lon": "118° 24.9' W",
    "depth": 150,
    "course": 342.5
}

current_noise_data = {
    "angle": 0.0, 
    "intensity": 0.0,
    "frequencies": [],
    "dominant_freq": 0.0,
    "detected_sounds": [],
    "primary_threat": "NEUTRAL",
    "confidence": 0.0,
    "range_estimate": 0.0  
}

# Create panels
panels = [
    DraggablePanel(920, 20, 300, 180, "DETECTION MODE"),
    DraggablePanel(920, 210, 300, 220, "SYSTEM STATUS"),
    DraggablePanel(920, 440, 300, 200, "OWN SHIP DATA"),
    DraggablePanel(1240, 20, 340, 400, "TRACKED TARGETS"),
    DraggablePanel(1240, 430, 340, 150, "ACOUSTIC SENSOR"),
    DraggablePanel(1240, 590, 340, 280, "RECORDING CONTROL"),
    DraggablePanel(10, 20, 300, 250, "ANALYTICS DASHBOARD"),  
    DraggablePanel(320, 20, 250, 180, "MISSION CONTROL")      
]

dragged_panel = None

# Default theme
current_theme_name = "green"
theme = ColorTheme.get_theme(current_theme_name)

# Create directories for data storage
os.makedirs("recordings", exist_ok=True)
os.makedirs("sessions", exist_ok=True)
os.makedirs("screenshots", exist_ok=True)
os.makedirs("exports", exist_ok=True)

# Verify directories were created
print("[SYSTEM] Checking directories...")
for dir_name in ["recordings", "sessions", "screenshots", "exports"]:
    if os.path.exists(dir_name):
        print(f"  ✓ {dir_name}/")
    else:
        print(f"  ✗ {dir_name}/ (FAILED TO CREATE)")
        
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Advanced Naval Acoustic Radar - Multi-Mode System v2.0")
clock = pygame.time.Clock()