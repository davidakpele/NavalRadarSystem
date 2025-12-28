import pygame
import numpy as np
import sounddevice as sd
import math
from collections import deque
from scipy import signal, fft
import json
import datetime
import os
import random
import csv
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional
import threading

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

WIDTH, HEIGHT = 1600, 900
CENTER = (450, HEIGHT // 2)  
RADAR_RADIUS = 350 
RADAR_CENTER = (450, HEIGHT // 2)  
FPS = 60
FS = 44100 
CHANNELS = 2
CHUNK = 1024 

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


# ============================================================================
# SOUND SYSTEM
# ============================================================================

class SoundSystem:
    """Manages sound effects for the radar system"""
    
    def __init__(self):
        self.sounds = {}
        self.muted = False
        self.master_volume = 0.7
        self.detection_sounds_enabled = True  # Only play sounds for detections
        self.ambient_sounds_enabled = False   # Disable ambient background sounds
        self.sweep_sounds_enabled = False     # Disable sweep sounds
        
        # Initialize sound system with proper channels
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
            pygame.mixer.set_num_channels(16)
            self.sound_initialized = True
        except Exception as e:
            print(f"[SOUND] Failed to initialize sound system: {e}")
            self.sound_initialized = False
            return
        
        # Create synthetic sounds
        self._create_synthetic_sounds()
        
        # Start ambient sounds
        self.start_ambient()
        print("[SOUND] Sound system initialized")
    
    def _create_synthetic_sounds(self):
        """Create synthetic sounds using pygame"""
        if not self.sound_initialized:
            return
            
        try:
            # 1. Radar sweep sound (short beep that sweeps in pitch)
            sweep_length = 200  # ms
            sweep_samples = int(44100 * sweep_length / 1000)
            
            # Create frequency sweep from 800Hz to 1200Hz
            t = np.linspace(0, sweep_length/1000, sweep_samples, False)
            freq = np.linspace(800, 1200, sweep_samples)
            sweep_wave = 0.3 * np.sin(2 * np.pi * freq * t)
            
            # Convert to stereo (2 channels)
            sweep_stereo = np.column_stack((sweep_wave, sweep_wave))
            
            # Convert to pygame sound
            sweep_sound = pygame.sndarray.make_sound(
                (sweep_stereo * 32767).astype(np.int16)
            )
            self.sounds["sweep"] = sweep_sound
            
            # 2. Sonar ping (clean sine wave)
            ping_length = 100  # ms
            ping_samples = int(44100 * ping_length / 1000)
            
            t = np.linspace(0, ping_length/1000, ping_samples, False)
            ping_wave = 0.5 * np.sin(2 * np.pi * 1500 * t)  # 1500Hz ping
            
            # Apply envelope
            envelope = np.ones_like(ping_wave)
            envelope[:10] = np.linspace(0, 1, 10)  # Attack
            envelope[-20:] = np.linspace(1, 0, 20)  # Release
            ping_wave *= envelope
            
            # Convert to stereo
            ping_stereo = np.column_stack((ping_wave, ping_wave))
            
            ping_sound = pygame.sndarray.make_sound(
                (ping_stereo * 32767).astype(np.int16)
            )
            self.sounds["ping"] = ping_sound
            
            # 3. Sonar echo (softer, shorter)
            echo_length = 50  # ms
            echo_samples = int(44100 * echo_length / 1000)
            
            t = np.linspace(0, echo_length/1000, echo_samples, False)
            echo_wave = 0.2 * np.sin(2 * np.pi * 1200 * t)  # 1200Hz echo
            
            # Convert to stereo
            echo_stereo = np.column_stack((echo_wave, echo_wave))
            
            echo_sound = pygame.sndarray.make_sound(
                (echo_stereo * 32767).astype(np.int16)
            )
            self.sounds["echo"] = echo_sound
            
            # 4. Target lock (double beep)
            lock_length = 150  # ms
            lock_samples = int(44100 * lock_length / 1000)
            
            t = np.linspace(0, lock_length/1000, lock_samples, False)
            # Create two pulses
            lock_wave = np.zeros_like(t)
            
            # First pulse at 1000Hz
            pulse1_start = 0
            pulse1_end = int(0.3 * lock_samples)
            t1 = t[pulse1_start:pulse1_end] - t[pulse1_start]
            lock_wave[pulse1_start:pulse1_end] = 0.3 * np.sin(2 * np.pi * 1000 * t1)
            
            # Second pulse at 1200Hz
            pulse2_start = int(0.5 * lock_samples)
            pulse2_end = lock_samples
            t2 = t[pulse2_start:pulse2_end] - t[pulse2_start]
            lock_wave[pulse2_start:pulse2_end] = 0.3 * np.sin(2 * np.pi * 1200 * t2)
            
            # Convert to stereo
            lock_stereo = np.column_stack((lock_wave, lock_wave))
            
            lock_sound = pygame.sndarray.make_sound(
                (lock_stereo * 32767).astype(np.int16)
            )
            self.sounds["target_lock"] = lock_sound
            
            # 5. Warning sound (repeating beep)
            warning_length = 300  # ms
            warning_samples = int(44100 * warning_length / 1000)
            
            t = np.linspace(0, warning_length/1000, warning_samples, False)
            warning_wave = 0.4 * np.sin(2 * np.pi * 800 * t)
            
            # Convert to stereo
            warning_stereo = np.column_stack((warning_wave, warning_wave))
            
            warning_sound = pygame.sndarray.make_sound(
                (warning_stereo * 32767).astype(np.int16)
            )
            self.sounds["warning"] = warning_sound
            
            # 6. Interface click
            click_length = 30  # ms
            click_samples = int(44100 * click_length / 1000)
            
            click_wave = 0.1 * np.random.randn(click_samples)  # White noise click
            envelope = np.ones_like(click_wave)
            envelope[:5] = np.linspace(0, 1, 5)
            envelope[-10:] = np.linspace(1, 0, 10)
            click_wave *= envelope
            
            # Convert to stereo
            click_stereo = np.column_stack((click_wave, click_wave))
            
            click_sound = pygame.sndarray.make_sound(
                (click_stereo * 32767).astype(np.int16)
            )
            self.sounds["click"] = click_sound
            
            # 7. Active sonar pulse (deeper, longer)
            sonar_pulse_length = 500  # ms
            sonar_pulse_samples = int(44100 * sonar_pulse_length / 1000)
            
            t = np.linspace(0, sonar_pulse_length/1000, sonar_pulse_samples, False)
            # Frequency sweep from 300Hz to 1000Hz
            freq = np.linspace(300, 1000, sonar_pulse_samples)
            sonar_pulse_wave = 0.6 * np.sin(2 * np.pi * freq * t)
            
            # Convert to stereo
            sonar_pulse_stereo = np.column_stack((sonar_pulse_wave, sonar_pulse_wave))
            
            sonar_pulse_sound = pygame.sndarray.make_sound(
                (sonar_pulse_stereo * 32767).astype(np.int16)
            )
            self.sounds["sonar_pulse"] = sonar_pulse_sound
            
            # 8. Ambient radar room noise (stereo for more realism)
            ambient_length = 44100 * 2  # 2 seconds of ambient noise
            
            # Create slightly different noise for each channel
            ambient_left = 0.04 * np.random.randn(ambient_length)
            ambient_right = 0.04 * np.random.randn(ambient_length)
            
            # Add low frequency hum
            t = np.linspace(0, 2, ambient_length, False)
            hum_left = 0.02 * np.sin(2 * np.pi * 60 * t)  # 60Hz hum
            hum_right = 0.02 * np.sin(2 * np.pi * 60 * t + 0.1)  # Slightly out of phase
            
            ambient_left += hum_left
            ambient_right += hum_right
            
            # Add occasional static bursts
            for _ in range(10):
                burst_start = np.random.randint(0, ambient_length - 1000)
                burst_length = np.random.randint(100, 500)
                burst_left = 0.08 * np.random.randn(burst_length)
                burst_right = 0.08 * np.random.randn(burst_length)
                ambient_left[burst_start:burst_start+burst_length] += burst_left
                ambient_right[burst_start:burst_start+burst_length] += burst_right
            
            # Combine into stereo array
            ambient_stereo = np.column_stack((ambient_left, ambient_right))
            
            ambient_sound = pygame.sndarray.make_sound(
                (ambient_stereo * 32767).astype(np.int16)
            )
            self.sounds["ambient"] = ambient_sound
            
        except Exception as e:
            print(f"[SOUND] Error creating sounds: {e}")
            import traceback
            traceback.print_exc()
    
    def play_sound(self, sound_name, volume=1.0, loops=0):
        """Play a sound effect"""
        if self.muted or not self.sound_initialized or sound_name not in self.sounds:
            return
        
        try:
            sound = self.sounds[sound_name]
            channel = pygame.mixer.find_channel(True)
            
            if channel:
                channel.set_volume(self.master_volume * volume)
                channel.play(sound, loops)
                return channel
        except Exception as e:
            print(f"[SOUND] Error playing sound {sound_name}: {e}")
    
    def start_ambient(self):
        """Start ambient background sound"""
        if not self.muted and self.sound_initialized and "ambient" in self.sounds:
            try:
                self.ambient_channel = self.play_sound("ambient", volume=0.2, loops=-1)
            except Exception as e:
                print(f"[SOUND] Error starting ambient: {e}")
    
    def stop_ambient(self):
        """Stop ambient sound"""
        if hasattr(self, 'ambient_channel') and self.ambient_channel:
            try:
                self.ambient_channel.stop()
            except:
                pass
    
    def play_radar_sweep(self):
        """Play radar sweep sound based on mode - MODIFIED: Only if enabled"""
        if not self.sound_initialized or not self.sweep_sounds_enabled:
            return
            
        config = ModeConfig.get_config(current_mode)
        
        if current_mode == DetectionMode.PASSIVE:
            # Soft sweep for passive
            self.play_sound("sweep", volume=0.3)
        elif current_mode == DetectionMode.ACTIVE_SONAR:
            # No sweep for active sonar (uses pings)
            pass
        elif current_mode == DetectionMode.WIDE_BEAM:
            # Faster sweep
            self.play_sound("sweep", volume=0.4)
        elif current_mode == DetectionMode.NARROW_BEAM:
            # Slower, more focused sweep
            self.play_sound("sweep", volume=0.5)
        elif current_mode == DetectionMode.OMNI_360:
            # Pulsing sound for omni
            self.play_sound("ping", volume=0.2)
    
    def play_target_detection(self, target_threat, intensity=None):
        """Play sound for target detection based on threat level"""
        if not self.sound_initialized or not self.detection_sounds_enabled:
            return
        
        # Default volumes
        volumes = {
            "HOSTILE": 0.7,
            "UNKNOWN": 0.5,
            "FRIENDLY": 0.3,
            "NEUTRAL": 0.2
        }
        
        base_volume = volumes.get(target_threat, 0.3)
        
        # Adjust volume based on intensity if provided
        if intensity is not None:
            base_volume = min(0.8, base_volume * (1.0 + intensity))
        
        if target_threat == "HOSTILE":
            self.play_sound("warning", volume=base_volume)
            # Also play ping for immediate feedback
            self.play_sound("ping", volume=base_volume * 0.8)
        elif target_threat == "UNKNOWN":
            self.play_sound("ping", volume=base_volume)
        elif target_threat == "FRIENDLY":
            self.play_sound("ping", volume=base_volume)
        else:  # NEUTRAL
            self.play_sound("ping", volume=base_volume)
    
    def play_sonar_pulse(self):
        """Play active sonar pulse sound"""
        if self.sound_initialized:
            self.play_sound("sonar_pulse", volume=0.8)
    
    def play_sonar_echo(self, strength):
        """Play sonar echo return"""
        if self.sound_initialized:
            volume = min(0.6, strength * 0.7)
            self.play_sound("echo", volume=volume)
    
    def play_ui_click(self):
        """Play UI interaction sound"""
        if self.sound_initialized:
            self.play_sound("click", volume=0.15)
    
    def play_mode_change(self):
        """Play sound for mode change"""
        if self.sound_initialized:
            self.play_sound("click", volume=0.25)
    
    def play_target_lock(self):
        """Play sound when target is selected"""
        if self.sound_initialized:
            self.play_sound("target_lock", volume=0.5)
    
    def toggle_mute(self):
        """Toggle sound on/off"""
        if not self.sound_initialized:
            print("[SOUND] Sound system not initialized")
            return
            
        self.muted = not self.muted
        if self.muted:
            pygame.mixer.pause()
            print("[SOUND] Muted")
        else:
            pygame.mixer.unpause()
            print("[SOUND] Unmuted")
    
    def set_volume(self, volume):
        """Set master volume (0.0 to 1.0)"""
        if not self.sound_initialized:
            return
            
        self.master_volume = max(0.0, min(1.0, volume))
        pygame.mixer.set_volume(self.master_volume)

# Initialize sound system with error handling
try:
    sound_system = SoundSystem()
except Exception as e:
    print(f"[ERROR] Failed to initialize sound system: {e}")
    print("[INFO] Continuing without sound...")
    # Create a dummy sound system
    class DummySoundSystem:
        def __init__(self): 
            self.muted = True
            self.master_volume = 0
            self.sound_initialized = False
        def play_sound(self, *args, **kwargs): pass
        def start_ambient(self): pass
        def stop_ambient(self): pass
        def play_radar_sweep(self): pass
        def play_target_detection(self, *args): pass
        def play_sonar_pulse(self): pass
        def play_sonar_echo(self, *args): pass
        def play_ui_click(self): pass
        def play_mode_change(self): pass
        def play_target_lock(self): pass
        def toggle_mute(self): pass
        def set_volume(self, *args): pass
    sound_system = DummySoundSystem()
    
# ============================================================================
# COLOR THEMES
# ============================================================================
# Initialize sound system
sound_system = SoundSystem()

class ColorTheme:
    """Color theme definitions"""
    THEMES = {
        "green": {
            "primary": (0, 255, 65),
            "secondary": (0, 60, 20),
            "accent": (0, 255, 255),
            "warning": (255, 255, 0),
            "danger": (255, 50, 50),
            "bg": (5, 8, 5)
        },
        "blue": {
            "primary": (0, 191, 255),
            "secondary": (0, 20, 60),
            "accent": (173, 216, 230),
            "warning": (255, 215, 0),
            "danger": (255, 69, 0),
            "bg": (5, 5, 15)
        },
        "amber": {
            "primary": (255, 191, 0),
            "secondary": (60, 40, 0),
            "accent": (255, 215, 0),
            "warning": (255, 140, 0),
            "danger": (255, 0, 0),
            "bg": (15, 10, 0)
        },
        "red": {
            "primary": (255, 0, 0),
            "secondary": (60, 0, 0),
            "accent": (255, 100, 100),
            "warning": (255, 165, 0),
            "danger": (139, 0, 0),
            "bg": (15, 0, 0)
        },
        "custom": {
            "primary": (147, 112, 219),
            "secondary": (25, 25, 112),
            "accent": (186, 85, 211),
            "warning": (255, 215, 0),
            "danger": (220, 20, 60),
            "bg": (10, 10, 25)
        }
    }
    
    @staticmethod
    def get_theme(name):
        return ColorTheme.THEMES.get(name, ColorTheme.THEMES["green"])

# Default theme
current_theme_name = "green"
theme = ColorTheme.get_theme(current_theme_name)

# Convenience color access
def get_color(key):
    return theme[key]

# ============================================================================
# DETECTION MODES
# ============================================================================

class DetectionMode:
    PASSIVE = "PASSIVE"
    ACTIVE_SONAR = "ACTIVE_SONAR"
    WIDE_BEAM = "WIDE_BEAM"
    NARROW_BEAM = "NARROW_BEAM"
    OMNI_360 = "OMNI_360"

class ModeConfig:
    """Configuration for each detection mode"""
    
    @staticmethod
    def get_config(mode):
        configs = {
            DetectionMode.PASSIVE: {
                "name": "PASSIVE",
                "description": "Stealth listening",
                "detection_arc": 60,  
                "range_multiplier": 1.0,
                "accuracy": 0.7,
                "sweep_speed": 3,
                "color": get_color("primary"),
                "shows_true_distance": False,
                "pulse_enabled": False
            },
            DetectionMode.ACTIVE_SONAR: {
                "name": "ACTIVE SONAR",
                "description": "Pulse echo ranging",
                "detection_arc": 45,
                "range_multiplier": 2.0,
                "accuracy": 0.95,
                "sweep_speed": 2,
                "color": get_color("accent"),
                "shows_true_distance": True,
                "pulse_enabled": True
            },
            DetectionMode.WIDE_BEAM: {
                "name": "WIDE BEAM",
                "description": "Broad coverage",
                "detection_arc": 120,
                "range_multiplier": 0.7,
                "accuracy": 0.4,
                "sweep_speed": 4,
                "color": get_color("warning"),
                "shows_true_distance": False,
                "pulse_enabled": False
            },
            DetectionMode.NARROW_BEAM: {
                "name": "NARROW BEAM",
                "description": "Focused sector",
                "detection_arc": 30,
                "range_multiplier": 1.5,
                "accuracy": 0.9,
                "sweep_speed": 1,
                "color": (255, 165, 0),
                "shows_true_distance": False,
                "pulse_enabled": False
            },
            DetectionMode.OMNI_360: {
                "name": "360° OMNI",
                "description": "All directions",
                "detection_arc": 360,
                "range_multiplier": 0.5,
                "accuracy": 0.3,
                "sweep_speed": 0,  
                "color": (100, 150, 255),
                "shows_true_distance": False,
                "pulse_enabled": False
            }
        }
        return configs.get(mode, configs[DetectionMode.PASSIVE])

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class TargetData:
    """Data class for target information"""
    timestamp: float
    target_id: int
    bearing: float
    range_nm: float
    distance_pixels: float
    intensity: float
    velocity: float
    angular_velocity: float
    threat_level: str
    sound_types: List[str]
    detection_mode: str
    predicted_position: Optional[Tuple[float, float]] = None
    
    def to_dict(self):
        return asdict(self)

@dataclass
class SessionData:
    """Data class for session recording"""
    session_id: str
    start_time: float
    end_time: Optional[float] = None
    mode_history: List[Dict] = None
    target_history: List[Dict] = None
    audio_samples: List[np.ndarray] = None
    metadata: Dict = None
    
    def __post_init__(self):
        if self.mode_history is None:
            self.mode_history = []
        if self.target_history is None:
            self.target_history = []
        if self.audio_samples is None:
            self.audio_samples = []
        if self.metadata is None:
            self.metadata = {}

# ============================================================================
# 3D VISUALIZATION
# ============================================================================

class ThreeDVisualizer:
    """3D visualization mode for radar data"""
    
    def __init__(self):
        self.enabled = False
        self.camera_distance = 500
        self.camera_angle = 45
        self.camera_height = 200
        self.view_mode = "perspective"  # "perspective" or "topdown"
        self.rotate_speed = 0.5
        
    def toggle(self):
        """Toggle 3D mode"""
        self.enabled = not self.enabled
        print(f"[3D] Mode {'enabled' if self.enabled else 'disabled'}")
        
    def draw_3d_radar(self, screen, targets, sweep_angle):
        """Draw 3D radar visualization"""
        if not self.enabled:
            return
            
        # Create 3D surface
        surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        
        # Draw 3D grid
        self._draw_3d_grid(surf)
        
        # Draw targets in 3D
        for target in targets.values():
            self._draw_3d_target(surf, target)
        
        # Draw 3D sweep line
        self._draw_3d_sweep(surf, sweep_angle)
        
        # Apply to screen
        screen.blit(surf, (0, 0))
        
    def _draw_3d_grid(self, surf):
        """Draw 3D grid"""
        center_x, center_y = WIDTH // 2, HEIGHT // 2
        
        # Draw depth circles
        for i in range(1, 6):
            radius = 50 * i
            for angle in range(0, 360, 30):
                x = center_x + radius * math.cos(math.radians(angle))
                y = center_y - radius * math.sin(math.radians(angle)) * 0.5  # Perspective compression
                depth = i * 0.2
                alpha = int(255 * (1 - depth))
                color = (*get_color("primary")[:3], alpha)
                pygame.draw.circle(surf, color, (int(x), int(y)), 2)
    
    def _draw_3d_target(self, surf, target):
        """Draw target in 3D"""
        center_x, center_y = WIDTH // 2, HEIGHT // 2
        
        # Convert to 3D coordinates
        distance = target.distance
        angle = target.angle
        depth = distance / RADAR_RADIUS
        
        # Perspective projection
        x = center_x + distance * math.cos(math.radians(angle - 90))
        y = center_y - distance * math.sin(math.radians(angle - 90)) * (0.5 + depth * 0.3)
        
        # Size based on intensity and depth
        size = max(4, int(8 * target.intensity * (1 - depth * 0.5)))
        
        # Color based on threat with depth fading
        color = target.get_color()
        faded_color = (*color[:3], int(color[3] * (1 - depth * 0.5)))
        
        # Draw target
        pygame.draw.circle(surf, faded_color, (int(x), int(y)), size)
        
        # Draw depth line
        pygame.draw.line(surf, faded_color, (int(x), int(y)), 
                        (int(x), int(y + size * 2)), 2)
    
    def _draw_3d_sweep(self, surf, sweep_angle):
        """Draw 3D sweep line"""
        center_x, center_y = WIDTH // 2, HEIGHT // 2
        
        # Calculate 3D sweep line
        length = RADAR_RADIUS
        x = center_x + length * math.cos(math.radians(sweep_angle - 90))
        y = center_y - length * math.sin(math.radians(sweep_angle - 90)) * 0.7
        
        # Draw sweep line with gradient
        for i in range(10):
            segment_length = length * (i + 1) / 10
            segment_x = center_x + segment_length * math.cos(math.radians(sweep_angle - 90))
            segment_y = center_y - segment_length * math.sin(math.radians(sweep_angle - 90)) * 0.7
            alpha = int(255 * (1 - i / 10))
            color = (*get_color("accent")[:3], alpha)
            pygame.draw.line(surf, color, (center_x, center_y), 
                            (int(segment_x), int(segment_y)), 2)

# Initialize 3D visualizer
visualizer_3d = ThreeDVisualizer()


# ============================================================================
# ADVANCED DATA ANALYTICS
# ============================================================================

class DataAnalyzer:
    """Advanced analytics for radar data"""
    
    def __init__(self):
        self.history_length = 1000
        self.target_history = deque(maxlen=self.history_length)
        self.mode_history = deque(maxlen=100)
        self.statistics = {}
        
    def add_target_data(self, target):
        """Add target data for analysis"""
        self.target_history.append({
            'timestamp': time.time(),
            'id': target.id,
            'bearing': target.angle,
            'range': target.distance,
            'velocity': target.velocity,
            'threat': target.threat_level,
            'intensity': target.intensity
        })
        
    def analyze_trajectories(self):
        """Analyze target trajectories"""
        if len(self.target_history) < 10:
            return {}
            
        # Group by target ID
        targets_by_id = {}
        for entry in self.target_history:
            target_id = entry['id']
            if target_id not in targets_by_id:
                targets_by_id[target_id] = []
            targets_by_id[target_id].append(entry)
        
        # Calculate trajectory statistics
        trajectories = {}
        for target_id, entries in targets_by_id.items():
            if len(entries) < 3:
                continue
                
            # Calculate movement patterns
            bearings = [e['bearing'] for e in entries]
            ranges = [e['range'] for e in entries]
            velocities = [e['velocity'] for e in entries]
            
            # Calculate trends
            bearing_trend = np.polyfit(range(len(bearings)), bearings, 1)[0]
            range_trend = np.polyfit(range(len(ranges)), ranges, 1)[0]
            
            trajectories[target_id] = {
                'id': target_id,
                'bearing_trend': bearing_trend,
                'range_trend': range_trend,
                'avg_velocity': np.mean(velocities),
                'max_velocity': np.max(velocities),
                'threat': entries[-1]['threat'],
                'data_points': len(entries)
            }
        
        return trajectories
    
    def predict_collisions(self, trajectories, time_ahead=10):
        """Predict potential collisions"""
        collisions = []
        target_ids = list(trajectories.keys())
        
        for i, id1 in enumerate(target_ids):
            for id2 in target_ids[i+1:]:
                traj1 = trajectories[id1]
                traj2 = trajectories[id2]
                
                # Simple linear prediction
                # This would need more sophisticated algorithms for real use
                bearing_diff = abs(traj1['bearing_trend'] - traj2['bearing_trend'])
                range_diff = abs(traj1['range_trend'] - traj2['range_trend'])
                
                if bearing_diff < 5 and range_diff < 20:  # Threshold values
                    collision_probability = min(0.9, (5 - bearing_diff) / 5 * 0.5 + 
                                                (20 - range_diff) / 20 * 0.5)
                    
                    if collision_probability > 0.3:
                        collisions.append({
                            'target1': id1,
                            'target2': id2,
                            'probability': collision_probability,
                            'eta_seconds': time_ahead
                        })
        
        return collisions
    
    def generate_heatmap(self):
        """Generate heatmap of target activity"""
        heatmap = np.zeros((360, 100))  # 360 degrees x 100 range bins
        
        for entry in self.target_history:
            bearing = int(entry['bearing']) % 360
            range_bin = int(min(entry['range'] / RADAR_RADIUS * 100, 99))
            heatmap[bearing][range_bin] += 1
        
        return heatmap
    
    def calculate_statistics(self):
        """Calculate overall statistics"""
        if len(self.target_history) == 0:
            return {}
        
        threats = [entry['threat'] for entry in self.target_history]
        velocities = [entry['velocity'] for entry in self.target_history]
        intensities = [entry['intensity'] for entry in self.target_history]
        
        stats = {
            'total_detections': len(self.target_history),
            'unique_targets': len(set(entry['id'] for entry in self.target_history)),
            'threat_distribution': {
                'HOSTILE': threats.count('HOSTILE'),
                'UNKNOWN': threats.count('UNKNOWN'),
                'NEUTRAL': threats.count('NEUTRAL'),
                'FRIENDLY': threats.count('FRIENDLY')
            },
            'avg_velocity': np.mean(velocities) if velocities else 0,
            'max_velocity': np.max(velocities) if velocities else 0,
            'avg_intensity': np.mean(intensities) if intensities else 0,
            'activity_level': min(1.0, len(self.target_history) / 100)  # 0-1 scale
        }
        
        return stats

# Initialize data analyzer
data_analyzer = DataAnalyzer()

# ============================================================================
# MISSION SCENARIO SCRIPTING
# ============================================================================

class MissionScenario:
    """Mission scenario scripting system"""
    
    def __init__(self):
        self.active_scenario = None
        self.scenarios = {}
        self.load_scenarios()
        self.current_step = 0
        self.scenario_timer = 0
        self.scenario_running = False
        
    def load_scenarios(self):
        """Load available scenarios"""
        self.scenarios = {
            "training": {
                "name": "Basic Training",
                "description": "Learn radar operation with simulated targets",
                "steps": [
                    {"time": 0, "action": "spawn", "type": "FRIENDLY", "angle": 45, "range": 0.3},
                    {"time": 5, "action": "spawn", "type": "NEUTRAL", "angle": 90, "range": 0.5},
                    {"time": 10, "action": "spawn", "type": "UNKNOWN", "angle": 135, "range": 0.7},
                    {"time": 15, "action": "spawn", "type": "HOSTILE", "angle": 180, "range": 0.9},
                    {"time": 25, "action": "message", "text": "Training complete!"}
                ]
            },
            "patrol": {
                "name": "Coastal Patrol",
                "description": "Patrol coastal waters for suspicious activity",
                "steps": [
                    {"time": 0, "action": "message", "text": "Begin coastal patrol"},
                    {"time": 3, "action": "spawn", "type": "FRIENDLY", "angle": 30, "range": 0.4},
                    {"time": 8, "action": "spawn", "type": "NEUTRAL", "angle": 120, "range": 0.6},
                    {"time": 15, "action": "spawn", "type": "HOSTILE", "angle": 210, "range": 0.8},
                    {"time": 20, "action": "spawn", "type": "HOSTILE", "angle": 300, "range": 0.5},
                    {"time": 30, "action": "message", "text": "Hostile convoy detected!"},
                    {"time": 35, "action": "objective", "text": "Track hostile targets"}
                ]
            },
            "search_rescue": {
                "name": "Search and Rescue",
                "description": "Locate and identify vessels in distress",
                "steps": [
                    {"time": 0, "action": "message", "text": "Begin search and rescue operation"},
                    {"time": 5, "action": "spawn", "type": "NEUTRAL", "angle": 60, "range": 0.3},
                    {"time": 10, "action": "spawn", "type": "FRIENDLY", "angle": 150, "range": 0.7, "distress": True},
                    {"time": 20, "action": "message", "text": "Distress signal detected!"},
                    {"time": 25, "action": "objective", "text": "Locate the vessel in distress"}
                ]
            },
            "custom": {
                "name": "Custom Scenario",
                "description": "Create your own scenario",
                "steps": []
            }
        }
    
    def start_scenario(self, scenario_name):
        """Start a mission scenario"""
        if scenario_name in self.scenarios:
            self.active_scenario = scenario_name
            self.current_step = 0
            self.scenario_timer = time.time()
            self.scenario_running = True
            print(f"[SCENARIO] Started: {self.scenarios[scenario_name]['name']}")
            return True
        return False
    
    def stop_scenario(self):
        """Stop current scenario"""
        self.scenario_running = False
        self.active_scenario = None
        print("[SCENARIO] Stopped")
    
    def update(self, target_manager):
        """Update scenario progression"""
        if not self.scenario_running or self.active_scenario is None:
            return
            
        scenario = self.scenarios[self.active_scenario]
        elapsed_time = time.time() - self.scenario_timer
        
        # Check for next step
        while (self.current_step < len(scenario["steps"]) and 
               elapsed_time >= scenario["steps"][self.current_step]["time"]):
            step = scenario["steps"][self.current_step]
            self.execute_step(step, target_manager)
            self.current_step += 1
        
        # Check if scenario complete
        if self.current_step >= len(scenario["steps"]):
            print(f"[SCENARIO] {scenario['name']} complete!")
            self.stop_scenario()
    
    def execute_step(self, step, target_manager):
        """Execute a scenario step"""
        action = step.get("action")
        
        if action == "spawn":
            # Spawn a target
            angle = step.get("angle", random.uniform(0, 360))
            distance = step.get("range", 0.5) * RADAR_RADIUS
            threat = step.get("type", "NEUTRAL")
            intensity = step.get("intensity", 0.5)
            
            sound_types = []
            if threat == "HOSTILE":
                sound_types = ["Engine High", "Propeller"]
            elif threat == "FRIENDLY":
                sound_types = ["Engine Low", "Navigation"]
            else:
                sound_types = ["Ambient Noise", "Machinery"]
            
            if step.get("distress"):
                sound_types.append("Distress Signal")
            
            target_manager.update_or_create(
                angle, distance, intensity,
                sound_types, threat, "SCENARIO"
            )
            
            print(f"[SCENARIO] Spawned {threat} target at {angle}°")
            
        elif action == "message":
            # Display message
            text = step.get("text", "")
            print(f"[SCENARIO MESSAGE] {text}")
            # Could add to on-screen message queue here
            
        elif action == "objective":
            # Set objective
            text = step.get("text", "")
            print(f"[SCENARIO OBJECTIVE] {text}")
    
    def create_custom_scenario(self, name, description, steps):
        """Create custom scenario"""
        self.scenarios["custom"] = {
            "name": name,
            "description": description,
            "steps": steps
        }
        print(f"[SCENARIO] Custom scenario '{name}' created")
    
    def save_scenario(self, filename):
        """Save scenario to file"""
        if self.active_scenario:
            with open(filename, 'w') as f:
                json.dump(self.scenarios[self.active_scenario], f, indent=2)
            print(f"[SCENARIO] Saved to {filename}")

# Initialize mission system
mission_system = MissionScenario()


# ============================================================================
# RECORDING & DATA LOGGING
# ============================================================================

class SessionRecorder:
    """Records and manages session data"""
    
    def __init__(self):
        self.recording = False
        self.session_data: Optional[SessionData] = None
        self.frame_buffer = []
        self.max_buffer_size = 3600  # 1 minute at 60 FPS
        self.audio_buffer = []
        self.record_audio = True
        self.record_video = True
        self.selective_recording = False
        
    def start_recording(self):
        """Start a new recording session"""
        session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_data = SessionData(
            session_id=session_id,
            start_time=time.time(),
            metadata={
                "version": "2.0",
                "screen_size": (WIDTH, HEIGHT),
                "fps": FPS,
                "theme": current_theme_name,
                "mode": current_mode
            }
        )
        self.recording = True
        self.frame_buffer = []
        self.audio_buffer = []
        print(f"[RECORDER] Started session: {session_id}")
        
    def stop_recording(self):
        """Stop recording and save session"""
        if not self.recording or not self.session_data:
            return None  # Only return if NOT recording
            
        self.recording = False
        self.session_data.end_time = time.time()
        
        # Save session data
        session_file = f"sessions/session_{self.session_data.session_id}.json"
        self._save_session(session_file)
        
        # Save video if enabled
        if self.record_video and len(self.frame_buffer) > 0:
            video_file = f"recordings/video_{self.session_data.session_id}.mp4"
            self._save_video(video_file)
        
        # Save audio if enabled
        if self.record_audio and len(self.audio_buffer) > 0:
            audio_file = f"recordings/audio_{self.session_data.session_id}.wav"
            self._save_audio(audio_file)
        
        print(f"[RECORDER] Stopped session: {self.session_data.session_id}")
        print(f"[RECORDER] Target events: {len(self.session_data.target_history)}")
        print(f"[RECORDER] Audio samples: {len(self.audio_buffer)}")
        print(f"[RECORDER] Frames buffered: {len(self.frame_buffer)}")
        
        # Print where files were saved
        print(f"[RECORDER] Session saved to: {session_file}")
        
        return self.session_data.session_id
          
    def add_frame(self, surface):
        """Add a frame to the recording buffer"""
        if not self.recording:
            return
            
        # Convert surface to array
        if len(self.frame_buffer) < self.max_buffer_size:
            frame_array = pygame.surfarray.array3d(surface)
            self.frame_buffer.append(frame_array)
    
    def add_audio(self, audio_data):
        """Add audio sample to buffer"""
        if not self.recording or not self.record_audio:
            return
            
        self.audio_buffer.append(audio_data.copy())
    
    def add_target_event(self, target_data: TargetData):
        """Log target detection event"""
        if not self.recording or not self.session_data:
            return
            
        self.session_data.target_history.append(target_data.to_dict())
    
    def add_mode_change(self, mode: str, timestamp: float):
        """Log mode change event"""
        if not self.recording or not self.session_data:
            return
            
        self.session_data.mode_history.append({
            "mode": mode,
            "timestamp": timestamp
        })
    
    def _save_session(self, filename):
        """Save session data to JSON"""
        try:
            # Create a simplified version without large arrays
            save_data = {
                "session_id": self.session_data.session_id,
                "start_time": self.session_data.start_time,
                "end_time": self.session_data.end_time,
                "duration": self.session_data.end_time - self.session_data.start_time,
                "mode_history": self.session_data.mode_history,
                "target_count": len(self.session_data.target_history),
                "targets": self.session_data.target_history[:100],  # Limit to first 100
                "frame_count": len(self.frame_buffer),
                "metadata": self.session_data.metadata
            }
            
            with open(filename, 'w') as f:
                json.dump(save_data, f, indent=2)
                
            # Save detailed target history separately
            if self.session_data.target_history:
                target_file = filename.replace('.json', '_targets.csv')
                self._export_targets_csv(target_file)
            
            print(f"[RECORDER] Session saved to {filename}")
        except Exception as e:
            print(f"[RECORDER] Error saving session: {e}")

    def _save_video(self, filename):
        """Save video frames (placeholder - requires opencv)"""
        print(f"[RECORDER] Video export to {filename} - requires opencv-python")
        print(f"[RECORDER] {len(self.frame_buffer)} frames buffered")
        # Note: Actual video encoding would require: pip install opencv-python
        # Example: cv2.VideoWriter to encode frames
        
    def _save_audio(self, filename):
        """Save audio buffer to WAV file"""
        try:
            import wave
            if len(self.audio_buffer) == 0:
                return
                
            audio_data = np.concatenate(self.audio_buffer)
            
            with wave.open(filename, 'w') as wav_file:
                wav_file.setnchannels(CHANNELS)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(FS)
                wav_file.writeframes((audio_data * 32767).astype(np.int16).tobytes())
                
            print(f"[RECORDER] Audio saved to {filename}")
        except Exception as e:
            print(f"[RECORDER] Error saving audio: {e}")
    
    def _export_targets_csv(self, filename):
        """Export target history to CSV"""
        try:
            if not self.session_data.target_history:
                return
                
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = list(self.session_data.target_history[0].keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for target in self.session_data.target_history:
                    writer.writerow(target)
                    
            print(f"[RECORDER] Target data exported to {filename}")
        except Exception as e:
            print(f"[RECORDER] Error exporting targets: {e}")

class DataExporter:
    """Handles various data export formats"""
    
    @staticmethod
    def export_csv(targets, filename):
        """Export current targets to CSV"""
        try:
            # Ensure exports directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = ['timestamp', 'id', 'bearing', 'range_nm', 'velocity', 
                             'threat_level', 'sound_types', 'intensity']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for target in targets.values():
                    writer.writerow({
                        'timestamp': datetime.datetime.now().isoformat(),
                        'id': target.id,
                        'bearing': f"{target.angle:.1f}",
                        'range_nm': f"{target.get_range_nm():.2f}",
                        'velocity': f"{target.velocity:.1f}",
                        'threat_level': target.threat_level,
                        'sound_types': ','.join(target.sound_types),
                        'intensity': f"{target.intensity:.2f}"
                    })
            print(f"[EXPORT] CSV exported to {filename}")
            print(f"[EXPORT] Saved {len(targets)} targets")
            return True
        except Exception as e:
            print(f"[EXPORT] Error exporting CSV: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def export_json(targets, filename):
        """Export current targets to JSON"""
        try:
            export_data = {
                "export_time": datetime.datetime.now().isoformat(),
                "target_count": len(targets),
                "targets": []
            }
            
            for target in targets.values():
                export_data["targets"].append({
                    "id": target.id,
                    "bearing": target.angle,
                    "range_nm": target.get_range_nm(),
                    "velocity": target.velocity,
                    "angular_velocity": target.angular_velocity,
                    "threat_level": target.threat_level,
                    "sound_types": target.sound_types,
                    "intensity": target.intensity,
                    "position_history": list(target.position_history)
                })
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
                
            print(f"[EXPORT] JSON exported to {filename}")
            return True
        except Exception as e:
            print(f"[EXPORT] Error: {e}")
            return False
    
    @staticmethod
    def generate_heatmap_data(target_history):
        """Generate heatmap data from target history"""
        heatmap = np.zeros((360, 100))  # 360 degrees x 100 range bins
        
        for target_data in target_history:
            bearing = int(target_data['bearing']) % 360
            range_bin = int(min(target_data['range_nm'] * 10, 99))
            heatmap[bearing][range_bin] += 1
        
        return heatmap

# ============================================================================
# AUDIO PROCESSING
# ============================================================================

audio_queue = deque(maxlen=100)
audio_recording_buffer = deque(maxlen=FS * 60)  # 60 seconds buffer
    
def audio_callback(indata, frames, time_info, status):
    """Audio callback function for real-time processing"""
    if status:
        print(f"Audio callback status: {status}")
    
    audio_queue.append(indata.copy())
    
    # Add to recording buffer if recording
    if recorder.recording and recorder.record_audio:
        audio_recording_buffer.append(indata.copy())

# Initialize audio stream
try:
    stream = sd.InputStream(
        callback=audio_callback,
        channels=CHANNELS,
        samplerate=FS,
        blocksize=CHUNK
    )
    audio_enabled = True
except Exception as e:
    print(f"Audio initialization error: {e}")
    audio_enabled = False
    stream = None

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

# Recording system
recorder = SessionRecorder()

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

# ============================================================================
# TARGET SYSTEM
# ============================================================================

class Target:
    """Advanced target with mode-specific properties"""
    next_id = 1
    
    def __init__(self, angle, distance, intensity, sound_types, threat_level, detection_mode):
        self.id = Target.next_id
        Target.next_id += 1
        
        # Convert to Python floats
        self.angle = float(angle)
        self.distance = float(distance)
        self.intensity = float(intensity)
        self.sound_types = sound_types
        self.threat_level = threat_level
        self.detection_mode = detection_mode
        
        # Position tracking
        self.position_history = deque(maxlen=50)
        self.position_history.append((self.angle, self.distance, pygame.time.get_ticks()))
        
        # Velocity - initialize with safe values
        self.velocity = 0.0
        
        # Initialize velocity_angle safely as float
        try:
            self.velocity_angle = float(math.radians(self.angle))
        except:
            self.velocity_angle = 0.0
        
        self.angular_velocity = 0.0
        
        # Prediction
        self.predicted_positions = []
        
        # Display
        self.alpha = 255
        self.last_update = pygame.time.get_ticks()
        self.trail_points = deque(maxlen=20)
        
        # Initialize with a valid trail point
        try:
            x = float(RADAR_CENTER[0] + self.distance * math.cos(math.radians(self.angle - 90)))
            y = float(RADAR_CENTER[1] + self.distance * math.sin(math.radians(self.angle - 90)))
            if not (math.isnan(x) or math.isnan(y)):
                self.trail_points.append((x, y))
        except Exception as e:
            print(f"[WARNING] Target {self.id}: Error initializing trail point: {e}")
        
        # Classification
        self.classification_confidence = 0.0
        self.possible_types = []
        
    def clean_trail_points(self):
        """Remove invalid points from trail"""
        if not hasattr(self, 'trail_points'):
            self.trail_points = deque(maxlen=20)
            return
        
        valid_points = deque(maxlen=20)
        for point in self.trail_points:
            # Check if point is a valid tuple with 2 numbers
            if (isinstance(point, (tuple, list)) and len(point) == 2 and
                isinstance(point[0], (int, float)) and isinstance(point[1], (int, float)) and
                not math.isnan(point[0]) and not math.isnan(point[1]) and
                math.isfinite(point[0]) and math.isfinite(point[1])):
                valid_points.append((float(point[0]), float(point[1])))
        self.trail_points = valid_points
     
    def update(self, angle, distance, intensity):
        """Update target position and calculate velocity"""
        current_time = pygame.time.get_ticks()
        
        # Convert to Python floats
        angle = float(angle)
        distance = float(distance)
        intensity = float(intensity)
        
        # Validate inputs
        if math.isnan(angle) or math.isnan(distance):
            print(f"[ERROR] Target {self.id} received NaN inputs: angle={angle}, distance={distance}")
            angle = 0.0
            distance = 0.0
        
        # Update position history
        self.position_history.append((angle, distance, current_time))
        
        # Calculate velocity if we have enough history
        if len(self.position_history) >= 2:
            old_angle, old_dist, old_time = self.position_history[-2]
            time_delta = (current_time - old_time) / 1000.0  # seconds
            
            if time_delta > 0 and time_delta < 10:  # Reasonable time delta check
                # Angular velocity
                angle_diff = angle - old_angle
                # Normalize angle difference to [-180, 180]
                while angle_diff > 180:
                    angle_diff -= 360
                while angle_diff < -180:
                    angle_diff += 360
                self.angular_velocity = float(angle_diff / time_delta)
                
                # Radial velocity
                dist_diff = distance - old_dist
                self.velocity = float(dist_diff / time_delta)
        
        # ALWAYS set velocity_angle to a valid float value
        try:
            self.velocity_angle = float(math.radians(angle))
        except:
            self.velocity_angle = 0.0
        
        self.angle = angle
        self.distance = distance
        self.intensity = intensity
        self.last_update = current_time
        self.alpha = 255
        
        # Add to trail with validation
        try:
            x = float(RADAR_CENTER[0] + distance * math.cos(math.radians(angle - 90)))
            y = float(RADAR_CENTER[1] + distance * math.sin(math.radians(angle - 90)))
            
            # Check for NaN values
            if not (math.isnan(x) or math.isnan(y)):
                self.trail_points.append((x, y))
            else:
                print(f"[WARNING] Target {self.id}: Skipping NaN trail point")
        except Exception as e:
            print(f"[ERROR] Target {self.id}: Error calculating trail point: {e}")
        
        # Predict future positions
        self.predict_future_positions()  
    
    def predict_future_positions(self, steps=5, time_step=2.0):
        """Predict future positions based on current velocity"""
        self.predicted_positions = []
        
        # Only predict if we have valid velocities
        if math.isnan(self.velocity) or math.isnan(self.angular_velocity):
            return
            
        if abs(self.velocity) < 0.1 and abs(self.angular_velocity) < 0.1:
            return
        
        pred_angle = self.angle
        pred_dist = self.distance
        
        for i in range(1, steps + 1):
            pred_angle += self.angular_velocity * time_step
            pred_dist += self.velocity * time_step
            
            pred_angle = pred_angle % 360
            pred_dist = max(0, min(pred_dist, RADAR_RADIUS))
            
            self.predicted_positions.append((pred_angle, pred_dist))
    
    def fade(self):
        """Fade target if not updated recently"""
        time_since_update = pygame.time.get_ticks() - self.last_update
        if time_since_update > 1000:
            self.alpha = max(0, 255 - (time_since_update - 1000) // 10)
            return self.alpha > 0
        return True
    
    def get_color(self):
        """Get color based on threat level"""
        colors = {
            "HOSTILE": get_color("danger"),
            "UNKNOWN": get_color("warning"),
            "NEUTRAL": get_color("primary"),
            "FRIENDLY": get_color("accent")
        }
        color = colors.get(self.threat_level, get_color("primary"))
        return (*color, self.alpha) if len(color) == 3 else color
    
    def get_range_nm(self):
        """Convert pixel distance to nautical miles"""
        return (self.distance / RADAR_RADIUS) * range_setting
    
    def get_position(self):
        """Get screen position with validation"""
        # Convert to Python floats
        angle = float(self.angle)
        distance = float(self.distance)
        
        # Check for invalid values
        if math.isnan(angle) or math.isnan(distance):
            print(f"[WARNING] Target {self.id} has invalid angle or distance")
            return (float(RADAR_CENTER[0]), float(RADAR_CENTER[1]))
        
        x = float(RADAR_CENTER[0] + distance * math.cos(math.radians(angle - 90)) * zoom_level)
        y = float(RADAR_CENTER[1] + distance * math.sin(math.radians(angle - 90)) * zoom_level)
        
        # Check for NaN results
        if math.isnan(x) or math.isnan(y):
            print(f"[WARNING] Target {self.id} position calculation resulted in NaN")
            return (float(RADAR_CENTER[0]), float(RADAR_CENTER[1]))
        
        return (x, y)
        
    def to_data(self):
        """Convert to TargetData for logging"""
        return TargetData(
            timestamp=time.time(),
            target_id=self.id,
            bearing=self.angle,
            range_nm=self.get_range_nm(),
            distance_pixels=self.distance,
            intensity=self.intensity,
            velocity=self.velocity,
            angular_velocity=self.angular_velocity,
            threat_level=self.threat_level,
            sound_types=self.sound_types,
            detection_mode=self.detection_mode
        )

class TargetManager:
    """Manages all targets"""
    
    def __init__(self):
        self.targets: Dict[int, Target] = {}
        self.selected_target: Optional[Target] = None
        self.collision_pairs = []
        self.target_size_filter = 0.0  # Minimum intensity to show
        
    def update_or_create(self, angle, distance, intensity, sound_types, threat_level, detection_mode):
        """Update existing target or create new one"""
        # Apply filters
        if intensity < self.target_size_filter:
            print(f"[FILTER] Target filtered out: intensity {intensity:.3f} < filter {self.target_size_filter:.3f}")
            return None
        
        # Apply gain control
        intensity *= gain_control
        
        # Find nearby target
        for target in self.targets.values():
            angle_diff = abs(target.angle - angle)
            if angle_diff > 180:
                angle_diff = 360 - angle_diff
            
            dist_diff = abs(target.distance - distance)
            
            if angle_diff < 10 and dist_diff < 30:
                target.update(angle, distance, intensity)
                target.sound_types = sound_types
                target.threat_level = threat_level
                
                # Log to recorder
                if recorder.recording:
                    recorder.add_target_event(target.to_data())
                
                print(f"[UPDATE] Updated target {target.id}")
                return target
        
        # Create new target
        new_target = Target(angle, distance, intensity, sound_types, threat_level, detection_mode)
        self.targets[new_target.id] = new_target
        
        # Log to recorder
        if recorder.recording:
            recorder.add_target_event(new_target.to_data())
        
        print(f"[CREATE] New target {new_target.id} created")
        return new_target
    
    def update_all(self):
        """Update all targets"""
        to_remove = []
        for target_id, target in self.targets.items():
            if not target.fade():
                to_remove.append(target_id)
        
        for target_id in to_remove:
            if self.selected_target and self.selected_target.id == target_id:
                self.selected_target = None
            del self.targets[target_id]
    
    def select_target_at(self, pos):
        """Select target at mouse position"""
        for target in self.targets.values():
            target_pos = target.get_position()
            dist = math.sqrt((pos[0] - target_pos[0])**2 + (pos[1] - target_pos[1])**2)
            if dist < 15:
                self.selected_target = target
                sound_system.play_target_lock()  # NEW
                return target
        
        self.selected_target = None
        return None
    
    def check_collisions(self):
        """Check for target collisions"""
        self.collision_pairs = []
        targets_list = list(self.targets.values())
        
        for i, t1 in enumerate(targets_list):
            for t2 in targets_list[i+1:]:
                dist = math.sqrt(
                    (t1.distance * math.cos(math.radians(t1.angle)) - 
                     t2.distance * math.cos(math.radians(t2.angle)))**2 +
                    (t1.distance * math.sin(math.radians(t1.angle)) - 
                     t2.distance * math.sin(math.radians(t2.angle)))**2
                )
                if dist < 20:
                    self.collision_pairs.append((t1, t2))
    
    def clear_all(self):
        """Clear all targets"""
        self.targets.clear()
        self.selected_target = None
        self.collision_pairs = []

target_manager = TargetManager()

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

# ============================================================================
# AUDIO ANALYSIS
# ============================================================================

def analyze_audio():
    """Analyze audio for target detection"""
    global current_noise_data
    
    if not audio_enabled or len(audio_queue) == 0:
        return
    
    try:
        audio_data = audio_queue[-1]
        
        # Stereo to mono
        if audio_data.shape[1] == 2:
            audio_mono = np.mean(audio_data, axis=1)
        else:
            audio_mono = audio_data[:, 0]
        
        # Calculate raw intensity BEFORE noise gate
        raw_intensity = np.sqrt(np.mean(audio_mono**2))
        
        # Apply gain control first
        audio_mono_amplified = audio_mono * gain_control
        
        # Apply frequency filter
        if frequency_filter == 'lowpass':
            sos = signal.butter(4, 2000, 'lp', fs=FS, output='sos')
            audio_mono_amplified = signal.sosfilt(sos, audio_mono_amplified)
        elif frequency_filter == 'highpass':
            sos = signal.butter(4, 500, 'hp', fs=FS, output='sos')
            audio_mono_amplified = signal.sosfilt(sos, audio_mono_amplified)
        elif frequency_filter == 'bandpass':
            sos = signal.butter(4, [500, 2000], 'bp', fs=FS, output='sos')
            audio_mono_amplified = signal.sosfilt(sos, audio_mono_amplified)
        
        # Calculate final intensity with much better scaling
        intensity = np.sqrt(np.mean(audio_mono_amplified**2))
        # Scale up significantly for better detection
        intensity = min(intensity * 10.0, 1.0)
        
        # Debug output every 30 frames (about twice per second at 60 FPS)
        if pygame.time.get_ticks() % 500 < 20:
            print(f"[AUDIO] Raw: {raw_intensity:.4f} | Intensity: {intensity:.4f} | Gate: {noise_gate:.2f}")
        
        # Apply noise gate AFTER amplification
        if intensity < noise_gate:
            current_noise_data["intensity"] = 0.0
            return
        
        # FFT analysis
        fft_data = np.fft.fft(audio_mono_amplified)
        freqs = np.fft.fftfreq(len(audio_mono_amplified), 1/FS)
        magnitudes = np.abs(fft_data)[:len(fft_data)//2]
        freqs = freqs[:len(freqs)//2]
        
        # Find dominant frequency
        if len(magnitudes) > 0:
            dominant_idx = np.argmax(magnitudes)
            dominant_freq = abs(freqs[dominant_idx])
        else:
            dominant_freq = 0.0
        
        # Stereo angle detection with better randomization
        if audio_data.shape[1] == 2:
            left = audio_data[:, 0]
            right = audio_data[:, 1]
            
            correlation = np.correlate(left, right, mode='same')
            delay = np.argmax(correlation) - len(correlation) // 2
            angle = (delay / len(correlation)) * math.pi
            # Add some variation
            angle += random.uniform(-0.3, 0.3)
        else:
            angle = random.uniform(0, 2 * math.pi)
        
        # Sound classification - adjusted for human voice (typically 85-255 Hz fundamental, harmonics 200-4000Hz)
        detected_sounds = []
        threat_level = "NEUTRAL"
        
        if dominant_freq < 100:
            detected_sounds.append({"type": "Low Frequency Rumble", "freq": dominant_freq})
            threat_level = "UNKNOWN"
        elif 100 <= dominant_freq < 300:
            detected_sounds.append({"type": "Voice/Engine Low", "freq": dominant_freq})
            threat_level = "UNKNOWN"
        elif 300 <= dominant_freq < 1000:
            detected_sounds.append({"type": "Voice/Machinery", "freq": dominant_freq})
            threat_level = "NEUTRAL"
        elif 1000 <= dominant_freq < 3000:
            detected_sounds.append({"type": "High Voice/Propeller", "freq": dominant_freq})
            threat_level = "HOSTILE"
        else:
            detected_sounds.append({"type": "High Frequency", "freq": dominant_freq})
            threat_level = "NEUTRAL"
        
        # Update global state
        current_noise_data.update({
            "angle": angle,
            "intensity": intensity,
            "frequencies": freqs.tolist()[:100],
            "dominant_freq": dominant_freq,
            "detected_sounds": detected_sounds,
            "primary_threat": threat_level,
            "confidence": min(intensity * 100, 100),
            "range_estimate": min(intensity * 15, RADAR_RADIUS * 0.9)
        })
        
    except Exception as e:
        print(f"[AUDIO] Analysis error: {e}")
        import traceback
        traceback.print_exc()

# ============================================================================
# UI PANELS
# ============================================================================

class DraggablePanel:
    def __init__(self, x, y, width, height, title="Panel", collapsible=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.dragging = False
        self.drag_offset = (0, 0)
        self.visible = True
        self.collapsible = collapsible
        self.collapsed = False
        self.original_height = height
        self.collapsed_height = 25
        
    def handle_event(self, event):
        if not self.visible:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                title_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 25)
                if title_rect.collidepoint(event.pos):
                    # Check if clicked on collapse button
                    if self.collapsible:
                        collapse_rect = pygame.Rect(self.rect.x + self.rect.width - 20, self.rect.y + 5, 15, 15)
                        if collapse_rect.collidepoint(event.pos):
                            self.toggle_collapse()
                            return True
                    
                    self.dragging = True
                    self.drag_offset = (event.pos[0] - self.rect.x, event.pos[1] - self.rect.y)
                    return True
                    
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
                
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.rect.x = event.pos[0] - self.drag_offset[0]
                self.rect.y = event.pos[1] - self.drag_offset[1]
                self.rect.x = max(0, min(self.rect.x, WIDTH - self.rect.width))
                self.rect.y = max(0, min(self.rect.y, HEIGHT - self.rect.height))
                return True
                
        return False
    
    def toggle_collapse(self):
        """Toggle panel collapse state"""
        self.collapsed = not self.collapsed
        if self.collapsed:
            self.rect.height = self.collapsed_height
        else:
            self.rect.height = self.original_height
    
    def draw(self, screen):
        if not self.visible:
            return
            
        # Apply brightness
        bg_color = tuple(int(c * brightness) for c in get_color("bg"))
        border_color = tuple(int(c * brightness) for c in get_color("primary"))
        
        # Draw panel background
        pygame.draw.rect(screen, bg_color, self.rect)
        
        # Draw title bar
        title_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 25)
        title_bg = tuple(int(c * brightness * 0.3) for c in get_color("secondary"))
        pygame.draw.rect(screen, title_bg, title_rect)
        pygame.draw.rect(screen, border_color, title_rect, 1)
        
        # Draw title
        font_title = pygame.font.SysFont("Courier New", 13, bold=True)
        title_text = font_title.render(self.title, True, get_color("accent"))
        screen.blit(title_text, (self.rect.x + 10, self.rect.y + 5))
        
        # Draw collapse button
        if self.collapsible:
            collapse_symbol = "−" if not self.collapsed else "+"
            collapse_text = font_title.render(collapse_symbol, True, get_color("accent"))
            screen.blit(collapse_text, (self.rect.x + self.rect.width - 18, self.rect.y + 5))
        
        # Draw panel border
        pygame.draw.rect(screen, border_color, self.rect, 2)
        
        return title_rect

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


def draw_analytics_dashboard(panel):
    """Draw analytics dashboard panel"""
    if panel.collapsed:
        panel.draw(screen)
        return
        
    font_header = pygame.font.SysFont("Courier New", 10, bold=True)
    font_data = pygame.font.SysFont("Courier New", 9, bold=True)
    
    panel.draw(screen)
    
    y = panel.rect.y + 30
    
    # Get analytics
    trajectories = data_analyzer.analyze_trajectories()
    collisions = data_analyzer.predict_collisions(trajectories)
    stats = data_analyzer.calculate_statistics()
    
    # Statistics
    if stats:
        stats_text = [
            f"Detections: {stats['total_detections']}",
            f"Unique Targets: {stats['unique_targets']}",
            f"Activity: {stats['activity_level']*100:.0f}%",
            f"Avg Velocity: {stats['avg_velocity']:.1f}",
            f"Collision Risks: {len(collisions)}"
        ]
        
        for text in stats_text:
            text_surf = font_data.render(text, True, get_color("primary"))
            screen.blit(text_surf, (panel.rect.x + 10, y))
            y += 18
    
    y += 10
    
    # Threat distribution
    if 'threat_distribution' in stats:
        threat_text = font_header.render("THREAT DISTRIBUTION:", True, get_color("warning"))
        screen.blit(threat_text, (panel.rect.x + 10, y))
        y += 15
        
        threats = [
            ("HOSTILE", get_color("danger"), stats['threat_distribution'].get('HOSTILE', 0)),
            ("UNKNOWN", get_color("warning"), stats['threat_distribution'].get('UNKNOWN', 0)),
            ("NEUTRAL", get_color("primary"), stats['threat_distribution'].get('NEUTRAL', 0)),
            ("FRIENDLY", get_color("accent"), stats['threat_distribution'].get('FRIENDLY', 0))
        ]
        
        for threat_name, color, count in threats:
            bar_width = min(150, count * 20)
            pygame.draw.rect(screen, color, (panel.rect.x + 10, y, bar_width, 10))
            
            text = font_data.render(f"{threat_name}: {count}", True, color)
            screen.blit(text, (panel.rect.x + 20, y + 12))
            y += 25
    
    # Collision warnings
    if collisions:
        y += 10
        warning_text = font_header.render("COLLISION ALERTS:", True, get_color("danger"))
        screen.blit(warning_text, (panel.rect.x + 10, y))
        y += 15
        
        for collision in collisions[:3]:  # Show only first 3
            text = f"T{collision['target1']}-T{collision['target2']}: {collision['probability']*100:.0f}%"
            text_surf = font_data.render(text, True, get_color("danger"))
            screen.blit(text_surf, (panel.rect.x + 10, y))
            y += 15


def draw_mission_control(panel):
    """Draw mission control panel"""
    if panel.collapsed:
        panel.draw(screen)
        return
        
    font_header = pygame.font.SysFont("Courier New", 10, bold=True)
    font_data = pygame.font.SysFont("Courier New", 9, bold=True)
    
    panel.draw(screen)
    
    y = panel.rect.y + 30
    
    # Mission status
    status = "ACTIVE" if mission_system.scenario_running else "STANDBY"
    status_color = get_color("accent") if mission_system.scenario_running else get_color("primary")
    
    status_text = font_header.render(f"MISSION: {status}", True, status_color)
    screen.blit(status_text, (panel.rect.x + 10, y))
    y += 20
    
    if mission_system.scenario_running:
        scenario = mission_system.scenarios.get(mission_system.active_scenario, {})
        name_text = font_data.render(f"Name: {scenario.get('name', 'Unknown')}", True, get_color("primary"))
        screen.blit(name_text, (panel.rect.x + 10, y))
        y += 15
        
        progress = (mission_system.current_step / len(scenario.get('steps', [1]))) * 100
        progress_text = font_data.render(f"Progress: {progress:.0f}%", True, get_color("accent"))
        screen.blit(progress_text, (panel.rect.x + 10, y))
        y += 20
    
    # Scenario buttons (simulated)
    scenarios = ["training", "patrol", "search_rescue", "custom"]
    
    for i, scenario_name in enumerate(scenarios[:3]):  # Show first 3
        scenario = mission_system.scenarios.get(scenario_name, {})
        btn_text = f"[{i+1}] {scenario.get('name', 'Unknown')}"
        text_color = get_color("accent") if mission_system.active_scenario == scenario_name else get_color("primary")
        
        text = font_data.render(btn_text, True, text_color)
        screen.blit(text, (panel.rect.x + 10, y))
        y += 18
    
    # Controls
    y += 10
    controls = [
        "[M] Toggle Mission",
        "[N] Next Scenario",
        "[B] Toggle 3D Mode"
    ]
    
    for control in controls:
        text = font_data.render(control, True, get_color("primary"))
        screen.blit(text, (panel.rect.x + 10, y))
        y += 16
        
        
        
# ============================================================================
# RADAR DRAWING FUNCTIONS
# ============================================================================

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

def draw_grid():
    """Draw radar grid"""
    primary_color = tuple(int(c * brightness * 0.5) for c in get_color("primary"))
    
    # Radial lines every 30 degrees
    for angle in range(0, 360, 30):
        end_x = RADAR_CENTER[0] + (RADAR_RADIUS * zoom_level) * math.cos(math.radians(angle - 90))
        end_y = RADAR_CENTER[1] + (RADAR_RADIUS * zoom_level) * math.sin(math.radians(angle - 90))
        pygame.draw.line(screen, primary_color, RADAR_CENTER, (end_x, end_y), 1)

def draw_compass():
    """Draw compass rose"""
    font = pygame.font.SysFont("Courier New", 14, bold=True)
    primary_color = tuple(int(c * brightness) for c in get_color("primary"))
    
    directions = [
        (0, "N"), (45, "NE"), (90, "E"), (135, "SE"),
        (180, "S"), (225, "SW"), (270, "W"), (315, "NW")
    ]
    
    for angle, label in directions:
        offset = (RADAR_RADIUS + 30) * zoom_level
        x = RADAR_CENTER[0] + offset * math.cos(math.radians(angle - 90))
        y = RADAR_CENTER[1] + offset * math.sin(math.radians(angle - 90))
        
        text = font.render(label, True, primary_color)
        text_rect = text.get_rect(center=(x, y))
        screen.blit(text, text_rect)

def draw_crt_effect():
    """Draw CRT screen effect"""
    # Scanlines
    for y in range(0, HEIGHT, 3):
        pygame.draw.line(screen, (0, 0, 0, 50), (0, y), (WIDTH, y), 1)
    
    # Screen curvature (simulated with vignette)
    vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(vignette, (0, 0, 0, 100), (WIDTH//2, HEIGHT//2), 
                      int(min(WIDTH, HEIGHT) * 0.6))
    pygame.draw.circle(vignette, (0, 0, 0, 0), (WIDTH//2, HEIGHT//2), 
                      int(min(WIDTH, HEIGHT) * 0.4))
    screen.blit(vignette, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

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

def draw_target(target):
    """Draw a single target"""
    pos = target.get_position()
    color = target.get_color()
    
    # Convert pos to regular Python floats
    pos = (float(pos[0]), float(pos[1]))
    
    # Validate position
    if math.isnan(pos[0]) or math.isnan(pos[1]):
        print(f"[ERROR] Target {target.id} has NaN position: {pos}")
        return
    
    # Draw trail with validation
    if len(target.trail_points) > 1:
        trail_color = (*color[:3], 100)
        
        # Filter out invalid points from trail and convert to Python floats
        valid_trail_points = []
        for point in target.trail_points:
            # Check if point is valid and convert to Python floats
            try:
                if (isinstance(point, (tuple, list)) and len(point) == 2):
                    # Convert numpy types to Python floats
                    x = float(point[0])
                    y = float(point[1])
                    
                    if not (math.isnan(x) or math.isnan(y) or 
                           not math.isfinite(x) or not math.isfinite(y)):
                        valid_trail_points.append((x, y))
            except (TypeError, ValueError) as e:
                print(f"[WARNING] Target {target.id}: Invalid trail point conversion: {point} - {e}")
        
        # Only draw if we have at least 2 valid points
        if len(valid_trail_points) >= 2:
            try:
                pygame.draw.lines(screen, trail_color, False, valid_trail_points, 1)
            except Exception as e:
                print(f"[ERROR] Target {target.id}: Error drawing trail: {e}")
    
    # Draw target symbol
    size = 8
    if target_manager.selected_target == target:
        size = 12
        # Draw selection ring
        pygame.draw.circle(screen, get_color("accent"), (int(pos[0]), int(pos[1])), 20, 2)
    
    # Draw target icon based on threat
    if target.threat_level == "HOSTILE":
        # Triangle
        points = [
            (pos[0], pos[1] - size),
            (pos[0] - size, pos[1] + size),
            (pos[0] + size, pos[1] + size)
        ]
        # Convert points to integers for pygame
        int_points = [(int(p[0]), int(p[1])) for p in points]
        pygame.draw.polygon(screen, color, int_points)
    elif target.threat_level == "FRIENDLY":
        # Circle
        pygame.draw.circle(screen, color, (int(pos[0]), int(pos[1])), size)
    else:
        # Square
        rect = pygame.Rect(int(pos[0] - size//2), int(pos[1] - size//2), size, size)
        pygame.draw.rect(screen, color, rect)
    
    # Draw ID label
    font = pygame.font.SysFont("Courier New", 9, bold=True)
    id_text = font.render(f"T{target.id}", True, color)
    screen.blit(id_text, (int(pos[0] + 10), int(pos[1] - 10)))
    
    # Draw velocity vector - SIMPLIFIED with numpy type conversion
    if abs(target.velocity) > 1:
        vec_length = min(abs(target.velocity) * 2, 50)
        
        # Ensure velocity_angle is valid
        velocity_angle = float(target.velocity_angle)
        if math.isnan(velocity_angle) or not math.isfinite(velocity_angle):
            velocity_angle = 0.0
        
        # Calculate vector end point
        cos_val = math.cos(velocity_angle)
        sin_val = math.sin(velocity_angle)
        vec_end_x = pos[0] + vec_length * cos_val
        vec_end_y = pos[1] + vec_length * sin_val
        
        # Convert to Python floats
        vec_end_x = float(vec_end_x)
        vec_end_y = float(vec_end_y)
        
        # Draw if endpoints are valid
        if (not math.isnan(vec_end_x) and not math.isnan(vec_end_y) and
            math.isfinite(vec_end_x) and math.isfinite(vec_end_y)):
            
            # Convert to integers for pygame
            end_pos = (int(vec_end_x), int(vec_end_y))
            start_pos = (int(pos[0]), int(pos[1]))
            
            try:
                pygame.draw.line(screen, color, start_pos, end_pos, 2)
                
                # Optional: Draw arrow head
                arrow_size = 5
                arrow_angle = velocity_angle + math.pi
                arrow_points = [
                    end_pos,
                    (int(end_pos[0] + arrow_size * math.cos(arrow_angle + 0.5)),
                     int(end_pos[1] + arrow_size * math.sin(arrow_angle + 0.5))),
                    (int(end_pos[0] + arrow_size * math.cos(arrow_angle - 0.5)),
                     int(end_pos[1] + arrow_size * math.sin(arrow_angle - 0.5)))
                ]
                pygame.draw.polygon(screen, color, arrow_points)
            except Exception as e:
                # Silently skip if there's an error
                pass
    
    # Draw predicted positions
    for pred_angle, pred_dist in target.predicted_positions:
        if math.isnan(pred_angle) or math.isnan(pred_dist):
            continue
            
        try:
            pred_x = RADAR_CENTER[0] + pred_dist * math.cos(math.radians(pred_angle - 90)) * zoom_level
            pred_y = RADAR_CENTER[1] + pred_dist * math.sin(math.radians(pred_angle - 90)) * zoom_level
            
            pred_x = float(pred_x)
            pred_y = float(pred_y)
            
            if not (math.isnan(pred_x) or math.isnan(pred_y)):
                pred_color = (*color[:3], 100)
                pygame.draw.circle(screen, pred_color, (int(pred_x), int(pred_y)), 3)
        except Exception as e:
            # Silently skip
            pass


# ============================================================================
# PANEL DRAWING FUNCTIONS
# ============================================================================

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

def draw_acoustic_sensor(panel):
    """Draw acoustic sensor panel"""
    if panel.collapsed:
        panel.draw(screen)
        return
        
    font_data = pygame.font.SysFont("Courier New", 11, bold=True)
    panel.draw(screen)
    
    y = panel.rect.y + 30
    
    # Signal strength bar
    bar_width = int(current_noise_data["intensity"] * 250)
    bar_color = get_color("primary") if current_noise_data["intensity"] < 0.7 else get_color("danger")
    pygame.draw.rect(screen, bar_color, (panel.rect.x + 10, y, bar_width, 15))
    pygame.draw.rect(screen, get_color("primary"), (panel.rect.x + 10, y, 250, 15), 1)
    
    signal_text = font_data.render(f"{current_noise_data['intensity']:.2f}", True, get_color("accent"))
    screen.blit(signal_text, (panel.rect.x + 265, y))
    
    y += 25
    
    # Frequency and bearing
    info = [
        ("FREQ:", f"{int(current_noise_data['dominant_freq'])} Hz"),
        ("BEARING:", f"{math.degrees(current_noise_data['angle']):.1f}°"),
        ("CONF:", f"{current_noise_data['confidence']:.0f}%")
    ]
    
    for label, value in info:
        label_surf = font_data.render(label, True, get_color("primary"))
        value_surf = font_data.render(value, True, get_color("accent"))
        screen.blit(label_surf, (panel.rect.x + 10, y))
        screen.blit(value_surf, (panel.rect.x + 150, y))
        y += 20

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

# ============================================================================
# MAIN LOOP
# ============================================================================

def handle_keyboard_shortcuts(event):
    """Handle keyboard shortcuts"""
    global current_mode, narrow_beam_angle, paused, current_theme_name, theme
    global brightness, show_grid, show_compass, crt_effect, zoom_level
    global range_setting, gain_control, frequency_filter, noise_gate
    
    if event.key == pygame.K_ESCAPE:
        return False  # Exit
    
    # Mode selection (1-5)
    elif event.key == pygame.K_1:
        current_mode = DetectionMode.PASSIVE
        recorder.add_mode_change(current_mode, time.time())
        sound_system.play_mode_change()  # NEW
    elif event.key == pygame.K_2:
        current_mode = DetectionMode.ACTIVE_SONAR
        recorder.add_mode_change(current_mode, time.time())
        sound_system.play_mode_change()  # NEW
    elif event.key == pygame.K_3:
        current_mode = DetectionMode.WIDE_BEAM
        recorder.add_mode_change(current_mode, time.time())
        sound_system.play_mode_change()  # NEW
    elif event.key == pygame.K_4:
        current_mode = DetectionMode.NARROW_BEAM
        recorder.add_mode_change(current_mode, time.time())
        sound_system.play_mode_change()  # NEW
    elif event.key == pygame.K_5:
        current_mode = DetectionMode.OMNI_360
        recorder.add_mode_change(current_mode, time.time())
        sound_system.play_mode_change() 
    
    elif event.key == pygame.K_l:
        # Toggle all detection sounds
        sound_system.detection_sounds_enabled = not sound_system.detection_sounds_enabled
        status = "ENABLED" if sound_system.detection_sounds_enabled else "DISABLED"
        print(f"[SOUND] Detection sounds {status}")
        sound_system.play_ui_click()
    
    elif event.key == pygame.K_k:
        # Toggle sweep sounds
        sound_system.sweep_sounds_enabled = not sound_system.sweep_sounds_enabled
        status = "ENABLED" if sound_system.sweep_sounds_enabled else "DISABLED"
        print(f"[SOUND] Sweep sounds {status}")
        sound_system.play_ui_click()
        
    # Active sonar pulse
    elif event.key == pygame.K_SPACE:
        if current_mode == DetectionMode.ACTIVE_SONAR:
            send_sonar_pulse()
            sound_system.play_sonar_pulse()  # NEW
        else:
            paused = not paused
            sound_system.play_ui_click()  # NEW
    
    # Narrow beam control
    elif event.key == pygame.K_LEFT:
        narrow_beam_angle = (narrow_beam_angle - 5) % 360
        sound_system.play_ui_click()  # NEW
    elif event.key == pygame.K_RIGHT:
        narrow_beam_angle = (narrow_beam_angle + 5) % 360
        sound_system.play_ui_click()  # NEW
    
    # Recording controls
    elif event.key == pygame.K_r:
        if recorder.recording:
            recorder.stop_recording()
        else:
            recorder.start_recording()
        sound_system.play_ui_click()  # NEW
    
    elif event.key == pygame.K_s:
        # Screenshot
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshots/screenshot_{timestamp}.png"
        
        # Ensure directory exists
        os.makedirs("screenshots", exist_ok=True)
        
        try:
            pygame.image.save(screen, filename)
            print(f"[SCREENSHOT] Saved to {filename}")
            sound_system.play_ui_click()
        except Exception as e:
            print(f"[SCREENSHOT] Error saving: {e}")
    
    # Sound controls (NEW)
    elif event.key == pygame.K_v:
        sound_system.toggle_mute()
    elif event.key == pygame.K_UP:
        sound_system.set_volume(min(1.0, sound_system.master_volume + 0.1))
        print(f"[VOLUME] {sound_system.master_volume:.1f}")
    elif event.key == pygame.K_DOWN:
        sound_system.set_volume(max(0.0, sound_system.master_volume - 0.1))
        print(f"[VOLUME] {sound_system.master_volume:.1f}")
        
    # Export controls
    elif event.key == pygame.K_e:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exports/targets_{timestamp}.csv"
        DataExporter.export_csv(target_manager.targets, filename)
    
    elif event.key == pygame.K_j:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exports/targets_{timestamp}.json"
        DataExporter.export_json(target_manager.targets, filename)
    
    # Clear targets
    elif event.key == pygame.K_c:
        target_manager.clear_all()
        print("[SYSTEM] All targets cleared")
    
    # Theme switching (T + number)
    elif event.key == pygame.K_t:
        themes = list(ColorTheme.THEMES.keys())
        current_index = themes.index(current_theme_name)
        current_theme_name = themes[(current_index + 1) % len(themes)]
        theme = ColorTheme.get_theme(current_theme_name)
        print(f"[THEME] Switched to {current_theme_name}")
    
    # Visual controls
    elif event.key == pygame.K_b:
        brightness = min(1.0, brightness + 0.1)
    elif event.key == pygame.K_d:
        brightness = max(0.3, brightness - 0.1)
    elif event.key == pygame.K_g:
        show_grid = not show_grid
    elif event.key == pygame.K_o:
        show_compass = not show_compass
    elif event.key == pygame.K_x:
        crt_effect = not crt_effect
    
    # Zoom controls
    elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
        zoom_level = min(2.0, zoom_level + 0.1)
    elif event.key == pygame.K_MINUS:
        zoom_level = max(0.5, zoom_level - 0.1)
    elif event.key == pygame.K_0:
        zoom_level = 1.0
    
    # Range controls
    elif event.key == pygame.K_LEFTBRACKET:
        range_setting = max(5, range_setting - 5)
        print(f"[RANGE] {range_setting} NM")
    elif event.key == pygame.K_RIGHTBRACKET:
        range_setting = min(100, range_setting + 5)
        print(f"[RANGE] {range_setting} NM")
    
    # Gain control
    elif event.key == pygame.K_PERIOD:
        gain_control = min(3.0, gain_control + 0.1)
        print(f"[GAIN] {gain_control:.1f}x")
    elif event.key == pygame.K_COMMA:
        gain_control = max(0.1, gain_control - 0.1)
        print(f"[GAIN] {gain_control:.1f}x")
    
    # Frequency filter
    elif event.key == pygame.K_f:
        filters = [None, 'lowpass', 'highpass', 'bandpass']
        current_idx = filters.index(frequency_filter) if frequency_filter in filters else 0
        frequency_filter = filters[(current_idx + 1) % len(filters)]
        print(f"[FILTER] {frequency_filter if frequency_filter else 'NONE'}")
    
    # Noise gate
    elif event.key == pygame.K_n:
        noise_gate = min(0.9, noise_gate + 0.05)
        print(f"[NOISE GATE] {noise_gate:.2f}")
    elif event.key == pygame.K_m:
        noise_gate = max(0.0, noise_gate - 0.05)
        print(f"[NOISE GATE] {noise_gate:.2f}")
    
    # Target size filter
    elif event.key == pygame.K_u:
        target_manager.target_size_filter = min(1.0, target_manager.target_size_filter + 0.05)
        print(f"[SIZE FILTER] {target_manager.target_size_filter:.2f}")
    elif event.key == pygame.K_y:
        target_manager.target_size_filter = max(0.0, target_manager.target_size_filter - 0.05)
        print(f"[SIZE FILTER] {target_manager.target_size_filter:.2f}")
    # Help
    elif event.key == pygame.K_h:
        print_help()
        
    # 3D Mode
    elif event.key == pygame.K_b:
        visualizer_3d.toggle()
        sound_system.play_ui_click()
        
    # Mission Controls
    elif event.key == pygame.K_m:
        if mission_system.scenario_running:
            mission_system.stop_scenario()
        else:
            mission_system.start_scenario("training")
        sound_system.play_ui_click()
    
    elif event.key == pygame.K_n:
        # Cycle through scenarios
        scenarios = list(mission_system.scenarios.keys())
        if mission_system.active_scenario:
            current_index = scenarios.index(mission_system.active_scenario)
            next_scenario = scenarios[(current_index + 1) % len(scenarios)]
        else:
            next_scenario = scenarios[0]
        
        mission_system.start_scenario(next_scenario)
        sound_system.play_ui_click()
    
    # Export analytics
    elif event.key == pygame.K_a:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exports/analytics_{timestamp}.json"
        
        analytics_data = {
            "timestamp": time.time(),
            "statistics": data_analyzer.calculate_statistics(),
            "trajectories": data_analyzer.analyze_trajectories(),
            "collisions": data_analyzer.predict_collisions(data_analyzer.analyze_trajectories()),
            "heatmap": data_analyzer.generate_heatmap().tolist()
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(analytics_data, f, indent=2)
            print(f"[ANALYTICS] Exported to {filename}")
        except Exception as e:
            print(f"[ANALYTICS] Export error: {e}")
    
    return True

def print_help():
    """Print keyboard shortcuts help"""
    help_text = """
    ╔══════════════════════════════════════════════════════════════╗
    ║           ADVANCED NAVAL RADAR - KEYBOARD SHORTCUTS          ║
    ╠══════════════════════════════════════════════════════════════╣
    ║ DETECTION MODES:                                             ║
    ║   1-5      : Switch detection modes                          ║
    ║   SPACE    : Sonar pulse (Active mode) / Pause               ║
    ║   ←/→      : Adjust narrow beam angle                        ║
    ║                                                              ║
    ║ 3D VISUALIZATION:                                            ║
    ║   B        : Toggle 3D visualization mode                    ║
    ║                                                              ║
    ║ MISSION SYSTEM:                                              ║
    ║   M        : Start/Stop mission scenario                     ║
    ║   N        : Cycle through scenarios                         ║
    ║                                                              ║
    ║ ANALYTICS:                                                   ║
    ║   A        : Export analytics data                           ║
    ║                                                              ║
    ║ SOUND CONTROLS:                                              ║
    ║   V        : Toggle mute/unmute                              ║
    ║   ↑/↓      : Volume up/down                                  ║
    ║   L        : Toggle detection sounds                         ║
    ║   K        : Toggle sweep sounds                             ║
    ║                                                              ║
    ║ RECORDING:                                                   ║
    ║   R        : Start/Stop recording                            ║
    ║   S        : Take screenshot                                 ║
    ║   E        : Export targets to CSV                           ║
    ║   J        : Export targets to JSON                          ║
    ║   C        : Clear all targets                               ║
    ║                                                              ║
    ║ DISPLAY:                                                     ║
    ║   T        : Cycle color themes                              ║
    ║   B/D      : Brightness up/down                              ║
    ║   G        : Toggle grid                                     ║
    ║   O        : Toggle compass                                  ║
    ║   X        : Toggle CRT effect                               ║
    ║   +/-      : Zoom in/out                                     ║
    ║   0        : Reset zoom                                      ║
    ║   [/]      : Decrease/Increase range                         ║
    ║                                                              ║
    ║ AUDIO:                                                       ║
    ║   ,/.      : Gain control down/up                            ║
    ║   F        : Cycle frequency filters                         ║
    ║   N/M      : Noise gate up/down                              ║
    ║   Y/U      : Target size filter down/up                      ║
    ║                                                              ║
    ║ OTHER:                                                       ║
    ║   H        : Show this help                                  ║
    ║   ESC      : Exit                                            ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(help_text)
    
    
def main():
    """Main application loop"""
    global sweep_angle, current_mode, narrow_beam_angle, dragged_panel
    global zoom_level, paused, brightness, show_grid, show_compass, crt_effect
    global range_setting, gain_control, frequency_filter, noise_gate
    global current_theme_name, theme, WIDTH, HEIGHT, screen
    
    print("╔═══════════════════════════════════════════════════════╗")
    print("║  ADVANCED NAVAL ACOUSTIC RADAR SYSTEM v2.0            ║")
    print("╚═══════════════════════════════════════════════════════╝")
    print("\nPress H for keyboard shortcuts help")
    print("SOUND SYSTEM: Only plays for target detections\n")
    
    # Start audio stream if available
    if stream and audio_enabled:
        stream.start()
    
    # Variables for detection timing
    last_detection_time = {}  # Track last detection time per target
    
    running = True
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if not handle_keyboard_shortcuts(event):
                    running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    # Check panel interaction
                    panel_clicked = False
                    for panel in panels:
                        if panel.handle_event(event):
                            panel_clicked = True
                            dragged_panel = panel
                            sound_system.play_ui_click()
                            break
                    
                    # Select target if not on panel
                    if not panel_clicked:
                        target_manager.select_target_at(event.pos)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    for panel in panels:
                        panel.handle_event(event)
                    dragged_panel = None
            
            elif event.type == pygame.MOUSEMOTION:
                for panel in panels:
                    panel.handle_event(event)
            
            elif event.type == pygame.MOUSEWHEEL:
                # Zoom with mouse wheel
                zoom_level = max(0.5, min(2.0, zoom_level + event.y * 0.1))
            
            elif event.type == pygame.VIDEORESIZE:
                # Handle window resize
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        
        if paused:
            pygame.display.flip()
            clock.tick(FPS)
            continue
        
        # Audio analysis
        analyze_audio()
        
        # Process sonar echoes
        if current_mode == DetectionMode.ACTIVE_SONAR:
            process_sonar_echoes()
        
        # Update mission system
        mission_system.update(target_manager)
        
        # Update analytics
        for target in target_manager.targets.values():
            data_analyzer.add_target_data(target)
        
        
        # Draw radar (2D or 3D)
        if visualizer_3d.enabled:
            visualizer_3d.draw_3d_radar(screen, target_manager.targets, sweep_angle)
        else:
            draw_radar_background()
            draw_sweep_line()
            
            # Draw targets
            for target in target_manager.targets.values():
                draw_target(target)
                    
        # Draw radar
        draw_radar_background()
        draw_sweep_line()
        
        # Target detection and updates
        config = ModeConfig.get_config(current_mode)
        current_time = pygame.time.get_ticks()
        
        # Lower threshold for detection and add debug
        detection_threshold = 0.01  # Very low threshold
        
        if current_noise_data["intensity"] > detection_threshold and current_noise_data["detected_sounds"]:
            detected_angle = math.degrees(current_noise_data["angle"])
            
            # Debug output
            if pygame.time.get_ticks() % 1000 < 20:
                print(f"[DETECT] Angle: {detected_angle:.1f}° | Intensity: {current_noise_data['intensity']:.3f} | Freq: {current_noise_data['dominant_freq']:.0f}Hz")
            
            # Mode-specific detection logic
            should_detect = False
            
            if current_mode == DetectionMode.OMNI_360:
                should_detect = True
            elif current_mode == DetectionMode.NARROW_BEAM:
                angle_diff = abs(detected_angle - narrow_beam_angle)
                if angle_diff > 180:
                    angle_diff = 360 - angle_diff
                if angle_diff < config["detection_arc"] / 2:
                    should_detect = True
            elif current_mode == DetectionMode.WIDE_BEAM:
                angle_diff = abs((sweep_angle % 360) - (detected_angle % 360))
                if angle_diff > 180:
                    angle_diff = 360 - angle_diff
                if angle_diff < config["detection_arc"] / 2:
                    should_detect = True
            else:  # PASSIVE or ACTIVE_SONAR
                angle_diff = abs((sweep_angle % 360) - (detected_angle % 360))
                if angle_diff < 15 or angle_diff > 345:
                    should_detect = True
            
            if should_detect:
                dist = min(current_noise_data["intensity"] * 15 * config["range_multiplier"], RADAR_RADIUS * 0.9)
                types = [s["type"] for s in current_noise_data["detected_sounds"]]
                
                target = target_manager.update_or_create(
                    detected_angle,
                    dist,
                    current_noise_data["intensity"],
                    types,
                    current_noise_data["primary_threat"],
                    current_mode
                )
                
                if target:
                    print(f"[TARGET] Created/Updated target {target.id} at angle {detected_angle:.1f}°, distance {dist:.1f}")
                    
                    # PLAY SOUND ONLY WHEN TARGET IS DETECTED
                    
                    # Only play sound if enough time has passed since last detection for this target
                    # or if it's a new target
                    if (target.id not in last_detection_time or 
                        current_time - last_detection_time[target.id] > 1000):  # 1 second cooldown
                        
                        sound_system.play_target_detection(
                            target.threat_level, 
                            target.intensity
                        )
                        last_detection_time[target.id] = current_time
        
        # Update all targets
        target_manager.update_all()
        target_manager.check_collisions()
        
        # Draw targets
        for target in target_manager.targets.values():
            draw_target(target)
        
        # Draw UI panels
        for i, panel in enumerate(panels):
            if i == 0:
                draw_mode_selector(panel)
            elif i == 1:
                draw_system_status(panel)
            elif i == 2:
                draw_own_ship_data(panel)
            elif i == 3:
                draw_tracked_targets(panel)
            elif i == 4:
                draw_acoustic_sensor(panel)
            elif i == 5:
                draw_recording_control(panel)
            elif i == 6:
                    draw_analytics_dashboard(panel)  
            elif i == 7:
                draw_mission_control(panel)
                
        # Draw status bar
        font_status = pygame.font.SysFont("Courier New", 10, bold=True)
        status_items = [
            f"MODE: {current_mode}",
            f"TARGETS: {len(target_manager.targets)}",
            f"RANGE: {range_setting}NM",
            f"GAIN: {gain_control:.1f}x",
            f"ZOOM: {zoom_level:.1f}x",
            f"FPS: {int(clock.get_fps())}"
        ]
        status_text = " | ".join(status_items)
        status_surf = font_status.render(status_text, True, get_color("primary"))
        screen.blit(status_surf, (10, HEIGHT - 20))
        
        # Recording indicator
        if recorder.recording:
            rec_text = font_status.render("● REC", True, get_color("danger"))
            screen.blit(rec_text, (WIDTH - 80, HEIGHT - 20))
        
        # Add frame to recording
        if recorder.recording and recorder.record_video:
            recorder.add_frame(screen)
        
        # Update display
        pygame.display.flip()
        
        # Update sweep angle (silent - no sweep sounds)
        if config["sweep_speed"] > 0 and not paused:
            sweep_angle = (sweep_angle + config["sweep_speed"]) % 360
        
        clock.tick(FPS)
    
    # Cleanup
    if recorder.recording:
        recorder.stop_recording()
    
    if stream and audio_enabled:
        stream.stop()
        stream.close()
    
    pygame.quit()
    print("\n[SYSTEM] Radar system shutdown complete")

if __name__ == "__main__":
    main()