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
from enum import Enum
import threading
import queue
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
import colorsys
from PIL import Image

from test5.main import DraggablePanel, ModeConfig, MultiSoundClassifier, draw_acoustic_sensor, draw_mode_selector, draw_own_ship_data, draw_system_status, draw_tracked_targets, send_sonar_pulse  # For screenshot functionality

WIDTH, HEIGHT = 1600, 900
CENTER = (450, HEIGHT // 2)  
RADAR_RADIUS = 350 
RADAR_CENTER = (450, HEIGHT // 2)  
FPS = 60
FS = 44100 
CHANNELS = 2
CHUNK = 1024 
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
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Naval Acoustic Radar - Multi-Mode Detection System v2.0")
clock = pygame.time.Clock()

# Colors - Extended palette
GREEN = (0, 255, 65)
YELLOW = (255, 255, 0)
RED = (255, 50, 50)
DARK_GREEN = (0, 60, 20)
BLACK = (5, 8, 5)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
BLUE = (100, 150, 255)
PURPLE = (200, 100, 255)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
AMBER = (255, 191, 0)
DARK_BLUE = (0, 0, 60)
DARK_RED = (60, 0, 0)

# Color Themes
class ColorTheme(Enum):
    GREEN = "green"
    BLUE = "blue"
    AMBER = "amber"
    RED = "red"
    CUSTOM = "custom"

class GridStyle(Enum):
    CIRCULAR = "circular"
    SQUARE = "square"
    HEXAGONAL = "hexagonal"

class SweepStyle(Enum):
    SOLID = "solid"
    DASHED = "dashed"
    PULSING = "pulsing"
    TRAIL = "trail"

# Detection Modes
class DetectionMode:
    PASSIVE = "PASSIVE"
    ACTIVE_SONAR = "ACTIVE_SONAR"
    WIDE_BEAM = "WIDE_BEAM"
    NARROW_BEAM = "NARROW_BEAM"
    OMNI_360 = "OMNI_360"

# System state
current_mode = DetectionMode.PASSIVE
sweep_angle = 0
narrow_beam_angle = 0  
sonar_pulse_time = 0
sonar_echo_targets = []

# Theme and Appearance Settings
class AppearanceSettings:
    def __init__(self):
        self.color_theme = ColorTheme.GREEN
        self.brightness = 1.0
        self.grid_style = GridStyle.CIRCULAR
        self.sweep_style = SweepStyle.SOLID
        self.show_scanlines = True
        self.crt_effect = False
        self.custom_colors = {
            "background": (5, 8, 5),
            "grid": (0, 100, 0),
            "sweep": (0, 255, 65),
            "targets": (255, 255, 0),
            "text": (200, 255, 200)
        }
        self.target_icons = "circle"  # circle, square, triangle, diamond
        
    def get_colors(self):
        if self.color_theme == ColorTheme.GREEN:
            return {
                "background": (5, 8, 5),
                "grid": (0, 100, 0),
                "sweep": (0, 255, 65),
                "targets": (255, 255, 0),
                "text": (200, 255, 200)
            }
        elif self.color_theme == ColorTheme.BLUE:
            return {
                "background": (5, 8, 20),
                "grid": (0, 80, 150),
                "sweep": (100, 200, 255),
                "targets": (255, 200, 100),
                "text": (200, 220, 255)
            }
        elif self.color_theme == ColorTheme.AMBER:
            return {
                "background": (10, 8, 5),
                "grid": (100, 80, 0),
                "sweep": (255, 191, 0),
                "targets": (255, 100, 0),
                "text": (255, 220, 150)
            }
        elif self.color_theme == ColorTheme.RED:
            return {
                "background": (20, 5, 5),
                "grid": (100, 20, 20),
                "sweep": (255, 50, 50),
                "targets": (255, 150, 50),
                "text": (255, 200, 200)
            }
        else:
            return self.custom_colors

appearance = AppearanceSettings()
def audio_callback(indata, frames, time, status):
    global current_noise_data
    try:
        left = indata[:, 0]
        right = indata[:, 1]
        mono = (left + right) / 2.0
        intensity = np.linalg.norm(indata)
        
        if intensity > 0.01:
            correlation = np.correlate(left, right, mode='full')
            delay = np.argmax(correlation) - (len(left) - 1)
            raw_angle = (delay / 20) * (math.pi / 2)
            
            dominant_freq, top_freqs, magnitude, fft_freq = MultiSoundClassifier.analyze_audio(mono, FS)
            detected_sounds, primary_threat, avg_confidence = MultiSoundClassifier.detect_multiple_sounds(
                dominant_freq, magnitude, fft_freq, intensity
            )
            
            current_noise_data["angle"] = float(np.clip(raw_angle, -math.pi/2, math.pi/2))
            current_noise_data["intensity"] = float(intensity)
            current_noise_data["dominant_freq"] = float(dominant_freq)
            current_noise_data["frequencies"] = top_freqs.tolist() if len(top_freqs) > 0 else []
            current_noise_data["detected_sounds"] = detected_sounds
            current_noise_data["primary_threat"] = primary_threat
            current_noise_data["confidence"] = float(avg_confidence)
        else:
            current_noise_data["intensity"] = 0.0
            current_noise_data["detected_sounds"] = []
            current_noise_data["confidence"] = 0.0
    except Exception as e:
        pass

stream = sd.InputStream(channels=CHANNELS, samplerate=FS, callback=audio_callback, blocksize=CHUNK)

# Range settings
class RangeSettings:
    def __init__(self):
        self.available_ranges = [5, 10, 20, 50, 100]  # NM
        self.current_range_index = 1  # Start with 10 NM
        self.auto_range = True
        self.split_screen = False
        self.zoom_level = 1.0
        self.sector_zoom = None  # (angle, width)
        
    def get_current_range_nm(self):
        return self.available_ranges[self.current_range_index]
    
    def get_pixels_per_nm(self):
        return RADAR_RADIUS / self.get_current_range_nm()
    
    def zoom_in(self):
        self.zoom_level = min(4.0, self.zoom_level * 1.2)
        
    def zoom_out(self):
        self.zoom_level = max(0.25, self.zoom_level / 1.2)

range_settings = RangeSettings()

# Recording and logging
@dataclass
class SessionData:
    session_id: str
    start_time: datetime.datetime
    targets: List[Dict]
    audio_data: List[np.ndarray]
    screen_captures: List[np.ndarray]
    settings: Dict
    
class SessionRecorder:
    def __init__(self):
        self.is_recording = False
        self.current_session: Optional[SessionData] = None
        self.audio_queue = queue.Queue()
        self.screenshot_queue = queue.Queue()
        self.target_history = []
        self.video_writer = None
        self.audio_writer = None
        
    def start_recording(self):
        self.is_recording = True
        session_id = f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_session = SessionData(
            session_id=session_id,
            start_time=datetime.datetime.now(),
            targets=[],
            audio_data=[],
            screen_captures=[],
            settings={}
        )
        print(f"Started recording session: {session_id}")
        
    def stop_recording(self):
        self.is_recording = False
        print(f"Stopped recording. Session saved.")
        
    def add_target_data(self, target_data: Dict):
        if self.is_recording and self.current_session:
            self.current_session.targets.append(target_data)
            
    def add_audio_frame(self, audio_frame: np.ndarray):
        if self.is_recording and self.current_session:
            self.audio_queue.put(audio_frame.copy())
            
    def add_screenshot(self, screenshot: np.ndarray):
        if self.is_recording and self.current_session:
            self.screenshot_queue.put(screenshot.copy())
            
    def export_csv(self, filename: str = None):
        if not filename:
            filename = f"{self.current_session.session_id}_data.csv"
        
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['timestamp', 'target_id', 'angle', 'distance', 'intensity', 
                         'threat_level', 'velocity', 'sound_types', 'detection_mode']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for target_data in self.current_session.targets:
                writer.writerow(target_data)
                
    def export_json(self, filename: str = None):
        if not filename:
            filename = f"{self.current_session.session_id}_data.json"
            
        data = asdict(self.current_session)
        with open(filename, 'w') as jsonfile:
            json.dump(data, jsonfile, default=str, indent=2)
            
    def generate_report(self):
        if not self.current_session:
            return "No session data available"
            
        report = {
            "session_id": self.current_session.session_id,
            "duration": str(datetime.datetime.now() - self.current_session.start_time),
            "total_targets": len(self.current_session.targets),
            "threat_summary": {},
            "detection_mode_usage": {}
        }
        
        # Count threats
        for target in self.current_session.targets:
            threat = target.get('threat_level', 'UNKNOWN')
            report["threat_summary"][threat] = report["threat_summary"].get(threat, 0) + 1
            
        return report

recorder = SessionRecorder()

# Filtering and sensitivity
class AudioFilters:
    def __init__(self):
        self.gain = 1.0
        self.noise_gate_threshold = 0.1
        self.high_pass_freq = 20  # Hz
        self.low_pass_freq = 8000  # Hz
        self.band_pass = False
        self.adaptive_filtering = True
        self.background_noise = None
        self.target_size_threshold = 0.3
        
    def apply_filters(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        filtered = audio_data.copy()
        
        # Apply gain
        filtered *= self.gain
        
        # Apply noise gate
        if self.noise_gate_threshold > 0:
            filtered[np.abs(filtered) < self.noise_gate_threshold] = 0
            
        # Apply frequency filters if enabled
        if self.band_pass or self.high_pass_freq > 0 or self.low_pass_freq < sample_rate/2:
            nyquist = sample_rate / 2
            b, a = signal.butter(4, [self.high_pass_freq/nyquist, self.low_pass_freq/nyquist], 
                                btype='band' if self.band_pass else 'bandpass')
            filtered = signal.filtfilt(b, a, filtered)
            
        # Adaptive filtering (simple implementation)
        if self.adaptive_filtering:
            if self.background_noise is None:
                self.background_noise = np.mean(np.abs(filtered))
            else:
                self.background_noise = 0.99 * self.background_noise + 0.01 * np.mean(np.abs(filtered))
                # Subtract estimated background noise
                filtered = np.clip(filtered - self.background_noise, 0, None)
                
        return filtered

audio_filters = AudioFilters()

# Enhanced visualization components
class HeatMap:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = np.zeros((width, height))
        self.decay_rate = 0.95
        
    def add_detection(self, x: int, y: int, intensity: float = 1.0):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[x, y] = min(1.0, self.grid[x, y] + intensity)
            
    def update(self):
        self.grid *= self.decay_rate
        
    def get_color_at(self, x: int, y: int):
        if 0 <= x < self.width and 0 <= y < self.height:
            value = self.grid[x, y]
            # Color gradient from blue (cold) to red (hot)
            if value < 0.3:
                return (0, 0, int(value * 255))
            elif value < 0.6:
                return (int((value-0.3)/0.3 * 255), int((value-0.3)/0.3 * 255), 255)
            else:
                return (255, int((1.0-value)/0.4 * 255), 0)

heat_map = HeatMap(360, int(RADAR_RADIUS))

# Enhanced Target class with more features
class EnhancedTarget:
    next_id = 1
    
    def __init__(self, angle, distance, intensity, sound_types, threat_level, detection_mode):
        self.id = EnhancedTarget.next_id
        EnhancedTarget.next_id += 1
        
        self.angle = angle
        self.distance = distance
        self.intensity = intensity
        self.sound_types = sound_types
        self.threat_level = threat_level
        self.detection_mode = detection_mode
        self.confidence = 0.8
        
        # Enhanced tracking
        self.position_history = deque(maxlen=100)
        self.position_history.append((angle, distance, pygame.time.get_ticks()))
        
        # Enhanced prediction
        self.velocity = 0.0
        self.velocity_angle = 0.0
        self.acceleration = 0.0
        self.trajectory_confidence = 0.0
        
        # Display
        self.alpha = 255
        self.last_update = pygame.time.get_ticks()
        self.is_ghost = False
        self.ghost_start_time = 0
        self.selected = False
        self.icon_type = appearance.target_icons
        
        # Classification
        self.classification = self._classify_target()
        
        # Track data
        self.track_data = []
        self._add_track_entry()
    
    def _classify_target(self):
        """Classify target based on characteristics"""
        if self.threat_level == "THREAT":
            return "HOSTILE"
        elif "VOICE" in self.sound_types:
            return "HUMAN"
        elif "MUSIC" in self.sound_types:
            return "ENTERTAINMENT"
        elif self.velocity > 20:
            return "FAST_MOVER"
        elif self.distance < 50:
            return "CLOSE_CONTACT"
        else:
            return "UNKNOWN"
    
    def _add_track_entry(self):
        self.track_data.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "angle": self.angle,
            "distance": self.distance,
            "intensity": self.intensity,
            "sound_types": self.sound_types,
            "threat_level": self.threat_level,
            "detection_mode": self.detection_mode,
            "classification": self.classification,
            "velocity": self.velocity,
            "confidence": self.confidence
        })
    
    def update(self, angle, distance, intensity, sound_types, threat_level, detection_mode):
        current_time = pygame.time.get_ticks()
        
        # Calculate velocity and acceleration
        if len(self.position_history) > 0:
            last_angle, last_distance, last_time = self.position_history[-1]
            time_delta = (current_time - last_time) / 1000.0
            
            if time_delta > 0:
                # Convert to Cartesian for velocity calculation
                x1 = last_distance * math.cos(math.radians(last_angle))
                y1 = last_distance * math.sin(math.radians(last_angle))
                x2 = distance * math.cos(math.radians(angle))
                y2 = distance * math.sin(math.radians(angle))
                
                # Velocity
                vx = (x2 - x1) / time_delta
                vy = (y2 - y1) / time_delta
                new_velocity = math.sqrt(vx**2 + vy**2)
                
                # Acceleration
                if self.velocity > 0:
                    self.acceleration = (new_velocity - self.velocity) / time_delta
                
                self.velocity = new_velocity
                self.velocity_angle = math.degrees(math.atan2(vy, vx))
                
                # Trajectory confidence based on consistency
                if len(self.position_history) > 2:
                    self.trajectory_confidence = min(0.95, self.trajectory_confidence + 0.1)
        
        self.position_history.append((angle, distance, current_time))
        
        # Update properties
        self.angle = angle
        self.distance = distance
        self.intensity = intensity
        self.sound_types = sound_types
        self.threat_level = threat_level
        self.detection_mode = detection_mode
        self.confidence = min(0.95, self.confidence + 0.05)
        self.alpha = 255
        self.last_update = current_time
        self.is_ghost = False
        
        # Reclassify if necessary
        if intensity > 0.7 or self.velocity > 15:
            self.classification = self._classify_target()
        
        self._add_track_entry()
        
        # Update heat map
        grid_x = int(angle % 360)
        grid_y = int(distance * heat_map.height / RADAR_RADIUS)
        heat_map.add_detection(grid_x, grid_y, intensity)
    
    def get_predicted_positions(self, steps: int = 5) -> List[Tuple[float, float]]:
        """Predict future positions"""
        if len(self.position_history) < 2 or self.velocity < 1.0:
            return []
        
        predictions = []
        x = self.distance * math.cos(math.radians(self.angle))
        y = self.distance * math.sin(math.radians(self.angle))
        
        vx = self.velocity * math.cos(math.radians(self.velocity_angle))
        vy = self.velocity * math.sin(math.radians(self.velocity_angle))
        
        for t in range(1, steps + 1):
            # Simple linear prediction with acceleration
            pred_x = x + vx * t + 0.5 * self.acceleration * t**2
            pred_y = y + vy * t + 0.5 * self.acceleration * t**2
            
            pred_dist = math.sqrt(pred_x**2 + pred_y**2)
            pred_angle = math.degrees(math.atan2(pred_y, pred_x))
            
            predictions.append((pred_angle % 360, pred_dist))
        
        return predictions
    
    def get_position(self) -> Tuple[int, int]:
        angle_rad = math.radians(self.angle - 90)
        px = int(CENTER[0] + math.cos(angle_rad) * self.distance)
        py = int(CENTER[1] + math.sin(angle_rad) * self.distance)
        return (px, py)
    
    def get_color(self):
        colors = appearance.get_colors()
        base_color = colors["targets"]
        
        if self.is_ghost:
            return (150, 150, 150, self.alpha)
        elif self.selected:
            return WHITE + (self.alpha,)
        elif self.threat_level == "THREAT":
            return (255, 50, 50, self.alpha)
        elif self.threat_level == "FRIENDLY":
            return (50, 255, 50, self.alpha)
        else:
            # Color based on confidence
            r = int(base_color[0] * self.confidence)
            g = int(base_color[1] * self.confidence)
            b = int(base_color[2] * self.confidence)
            return (r, g, b, self.alpha)
    
    def fade(self) -> bool:
        """Update alpha for fading and return True if still visible"""
        time_since_update = pygame.time.get_ticks() - self.last_update
        
        if time_since_update > 1000 and not self.is_ghost:
            self.is_ghost = True
            self.ghost_start_time = pygame.time.get_ticks()
        
        if self.is_ghost:
            ghost_duration = pygame.time.get_ticks() - self.ghost_start_time
            if ghost_duration < 10000:  # 10 seconds ghost duration
                self.alpha = max(30, 255 - int((ghost_duration / 10000.0) * 225))
                return True
            else:
                return False
        
        if time_since_update > 100:
            self.alpha = max(0, self.alpha - 1)
        
        return self.alpha > 0

# Enhanced target manager
class EnhancedTargetManager:
    def __init__(self):
        self.targets: Dict[int, EnhancedTarget] = {}
        self.selected_target: Optional[EnhancedTarget] = None
        self.collision_warnings = []
        self.threat_levels = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
        
    def update_or_create(self, angle, distance, intensity, sound_types, threat_level, detection_mode):
        # Filter by target size threshold
        if intensity < audio_filters.target_size_threshold:
            return
            
        config = ModeConfig.get_config(detection_mode)
        detection_arc = config["detection_arc"]
        
        found_target = None
        for target in self.targets.values():
            angle_diff = abs(target.angle - angle)
            if angle_diff > 180:
                angle_diff = 360 - angle_diff
            
            dist_diff = abs(target.distance - distance)
            
            if angle_diff < detection_arc / 4 and dist_diff < 50:
                found_target = target
                break
        
        if found_target:
            found_target.update(angle, distance, intensity, sound_types, threat_level, detection_mode)
        else:
            new_target = EnhancedTarget(angle, distance, intensity, sound_types, threat_level, detection_mode)
            self.targets[new_target.id] = new_target
            
        # Update threat statistics
        self._update_threat_stats(threat_level)
        
        # Log to recorder
        if recorder.is_recording:
            recorder.add_target_data({
                "timestamp": datetime.datetime.now().isoformat(),
                "target_id": found_target.id if found_target else new_target.id,
                "angle": angle,
                "distance": distance,
                "intensity": intensity,
                "threat_level": threat_level,
                "velocity": found_target.velocity if found_target else 0,
                "sound_types": sound_types,
                "detection_mode": detection_mode
            })
    
    def _update_threat_stats(self, threat_level: str):
        if threat_level == "THREAT":
            self.threat_levels["HIGH"] += 1
        elif threat_level == "NEUTRAL":
            self.threat_levels["MEDIUM"] += 1
        else:
            self.threat_levels["LOW"] += 1
    
    def update_all(self):
        to_remove = []
        for tid, target in self.targets.items():
            if not target.fade():
                to_remove.append(tid)
        
        for tid in to_remove:
            del self.targets[tid]
    
    def select_target_at(self, pos: Tuple[int, int]) -> Optional[EnhancedTarget]:
        for target in self.targets.values():
            target_pos = target.get_position()
            distance = math.sqrt((pos[0]-target_pos[0])**2 + (pos[1]-target_pos[1])**2)
            if distance < 15:
                if self.selected_target:
                    self.selected_target.selected = False
                target.selected = True
                self.selected_target = target
                return target
        
        if self.selected_target:
            self.selected_target.selected = False
            self.selected_target = None
        return None
    
    def get_target_statistics(self) -> Dict:
        stats = {
            "total_targets": len(self.targets),
            "active_targets": sum(1 for t in self.targets.values() if not t.is_ghost),
            "ghost_targets": sum(1 for t in self.targets.values() if t.is_ghost),
            "threat_distribution": self.threat_levels.copy(),
            "average_confidence": np.mean([t.confidence for t in self.targets.values()]) if self.targets else 0,
            "max_velocity": max([t.velocity for t in self.targets.values()]) if self.targets else 0
        }
        return stats

target_manager = EnhancedTargetManager()

# Updated DraggablePanel with resize capability
class ResizablePanel(DraggablePanel):
    def __init__(self, x, y, width, height, title="Panel", color=BLACK, border_color=GREEN, min_width=100, min_height=50):
        super().__init__(x, y, width, height, title, color, border_color)
        self.min_width = min_width
        self.min_height = min_height
        self.resizing = False
        self.resize_corner = None
        self.resize_handle_size = 10
        
    def handle_event(self, event):
        handled = super().handle_event(event)
        
        if not self.visible:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check if mouse is over resize corner
            resize_rect = pygame.Rect(
                self.rect.right - self.resize_handle_size,
                self.rect.bottom - self.resize_handle_size,
                self.resize_handle_size,
                self.resize_handle_size
            )
            
            if resize_rect.collidepoint(event.pos):
                self.resizing = True
                self.resize_corner = (event.pos[0], event.pos[1])
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.resizing = False
            self.resize_corner = None
            
        elif event.type == pygame.MOUSEMOTION and self.resizing:
            dx = event.pos[0] - self.resize_corner[0]
            dy = event.pos[1] - self.resize_corner[1]
            
            new_width = max(self.min_width, self.rect.width + dx)
            new_height = max(self.min_height, self.rect.height + dy)
            
            self.rect.width = new_width
            self.rect.height = new_height
            self.resize_corner = (event.pos[0], event.pos[1])
            return True
            
        return handled
    
    def draw(self, screen):
        if not self.visible:
            return
            
        super().draw(screen)
        
        # Draw resize handle
        resize_rect = pygame.Rect(
            self.rect.right - self.resize_handle_size,
            self.rect.bottom - self.resize_handle_size,
            self.resize_handle_size,
            self.resize_handle_size
        )
        pygame.draw.rect(screen, CYAN, resize_rect, 1)
        pygame.draw.line(screen, CYAN, 
                        (self.rect.right - 7, self.rect.bottom - 3),
                        (self.rect.right - 3, self.rect.bottom - 7), 2)

# Create enhanced panels
panels = [
    ResizablePanel(500, 10, 280, 220, "DETECTION MODE", BLACK, GREEN),
    ResizablePanel(500, 240, 280, 140, "SYSTEM STATUS", BLACK, GREEN),
    ResizablePanel(500, 390, 280, 140, "OWN SHIP DATA", BLACK, GREEN),
    ResizablePanel(500, 540, 280, 350, "TRACKED TARGETS", BLACK, GREEN),
    ResizablePanel(WIDTH - 320, 10, 310, 120, "ACOUSTIC SENSOR", BLACK, GREEN),
]

# Add new panels for enhanced features
panels.append(ResizablePanel(WIDTH - 320, 140, 310, 120, "FILTERS & GAIN", BLACK, GREEN))
panels.append(ResizablePanel(WIDTH - 320, 270, 310, 180, "STATISTICS", BLACK, GREEN))
panels.append(ResizablePanel(WIDTH - 320, 460, 310, 150, "RECORDING", BLACK, GREEN))

# Visualization Tools
class VisualizationTools:
    def __init__(self):
        self.compass_visible = True
        self.mini_map_visible = True
        self.grid_visible = True
        self.bearing_lines = []
        self.measurement_lines = []
        self.coordinate_grid = False
        self.overlay_transparency = 0.5
        
    def draw_compass(self, screen):
        if not self.compass_visible:
            return
            
        compass_center = (WIDTH - 100, 100)
        compass_radius = 40
        
        # Draw compass circle
        pygame.draw.circle(screen, (50, 50, 50), compass_center, compass_radius)
        pygame.draw.circle(screen, WHITE, compass_center, compass_radius, 2)
        
        # Draw cardinal directions
        font = pygame.font.SysFont("Courier New", 12, bold=True)
        directions = ["N", "E", "S", "W"]
        
        for i, direction in enumerate(directions):
            angle = math.radians(i * 90)
            x = compass_center[0] + math.cos(angle) * (compass_radius - 15)
            y = compass_center[1] + math.sin(angle) * (compass_radius - 15)
            
            text = font.render(direction, True, WHITE)
            text_rect = text.get_rect(center=(x, y))
            screen.blit(text, text_rect)
        
        # Draw heading indicator
        heading_angle = math.radians(own_ship["heading"])
        end_x = compass_center[0] + math.cos(heading_angle) * (compass_radius - 5)
        end_y = compass_center[1] + math.sin(heading_angle) * (compass_radius - 5)
        pygame.draw.line(screen, RED, compass_center, (end_x, end_y), 3)
    
    def draw_mini_map(self, screen):
        if not self.mini_map_visible:
            return
            
        map_rect = pygame.Rect(WIDTH - 250, HEIGHT - 250, 240, 240)
        
        # Draw map background
        pygame.draw.rect(screen, (20, 20, 20), map_rect)
        pygame.draw.rect(screen, GREEN, map_rect, 2)
        
        # Draw title
        font = pygame.font.SysFont("Courier New", 12, bold=True)
        title = font.render("OVERVIEW MAP", True, CYAN)
        screen.blit(title, (map_rect.x + 10, map_rect.y + 5))
        
        # Draw simplified radar representation
        map_center = (map_rect.x + map_rect.width // 2, map_rect.y + map_rect.height // 2)
        map_radius = map_rect.width // 2 - 20
        
        pygame.draw.circle(screen, DARK_GREEN, map_center, map_radius, 1)
        
        # Draw targets on minimap
        for target in target_manager.targets.values():
            if target.is_ghost:
                continue
                
            # Convert to minimap coordinates
            angle_rad = math.radians(target.angle)
            dist_ratio = target.distance / RADAR_RADIUS
            x = map_center[0] + math.cos(angle_rad) * dist_ratio * map_radius
            y = map_center[1] + math.sin(angle_rad) * dist_ratio * map_radius
            
            color = target.get_color()
            pygame.draw.circle(screen, color[:3], (int(x), int(y)), 3)
    
    def draw_measurement_tools(self, screen):
        for line in self.measurement_lines:
            pygame.draw.line(screen, CYAN, line[0], line[1], 2)
            
            # Calculate and display distance
            dx = line[1][0] - line[0][0]
            dy = line[1][1] - line[0][1]
            distance_pixels = math.sqrt(dx**2 + dy**2)
            distance_nm = distance_pixels / range_settings.get_pixels_per_nm()
            
            # Display distance label
            mid_x = (line[0][0] + line[1][0]) // 2
            mid_y = (line[0][1] + line[1][1]) // 2
            font = pygame.font.SysFont("Courier New", 10, bold=True)
            text = font.render(f"{distance_nm:.1f} NM", True, CYAN)
            screen.blit(text, (mid_x + 5, mid_y + 5))
    
    def add_measurement_line(self, start_pos, end_pos):
        self.measurement_lines.append((start_pos, end_pos))
        
    def clear_measurements(self):
        self.measurement_lines.clear()

viz_tools = VisualizationTools()

# Screen capture functionality
class ScreenCapture:
    @staticmethod
    def capture_screen(filename=None):
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
        
        # Capture PyGame screen
        screenshot = pygame.image.tobytes(screen, 'RGB')
        img = Image.frombytes('RGB', (WIDTH, HEIGHT), screenshot)
        img.save(filename)
        print(f"Screenshot saved: {filename}")
        
        return screenshot
    
    @staticmethod
    def capture_region(rect: pygame.Rect, filename=None):
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"region_{timestamp}.png"
        
        # Create subsurface of the specified region
        subsurface = screen.subsurface(rect)
        screenshot = pygame.image.tostring(subsurface, 'RGB')
        img = Image.frombytes('RGB', rect.size, screenshot)
        img.save(filename)
        print(f"Region screenshot saved: {filename}")

# Enhanced drawing functions
def draw_enhanced_radar_background():
    colors = appearance.get_colors()
    
    # Apply brightness
    bg_color = tuple(int(c * appearance.brightness) for c in colors["background"])
    screen.fill(bg_color)
    
    config = ModeConfig.get_config(current_mode)
    
    radar_rect = pygame.Rect(RADAR_CENTER[0] - RADAR_RADIUS - 50, 
                             RADAR_CENTER[1] - RADAR_RADIUS - 50,
                             (RADAR_RADIUS + 50) * 2, 
                             (RADAR_RADIUS + 50) * 2)
    
    # Draw radar area with theme colors
    pygame.draw.rect(screen, bg_color, radar_rect)
    pygame.draw.rect(screen, colors["grid"], radar_rect, 2)
    
    # Draw grid based on selected style
    if appearance.grid_style == GridStyle.CIRCULAR:
        # Concentric circles
        for i in range(1, 5):
            radius = (RADAR_RADIUS // 4) * i
            pygame.draw.circle(screen, colors["grid"], RADAR_CENTER, radius, 1)
            
        # Radial lines
        for i in range(0, 360, 30):
            rad = math.radians(i)
            dest = (int(RADAR_CENTER[0] + math.cos(rad) * RADAR_RADIUS), 
                    int(RADAR_CENTER[1] + math.sin(rad) * RADAR_RADIUS))
            pygame.draw.line(screen, colors["grid"], RADAR_CENTER, dest, 1)
            
    elif appearance.grid_style == GridStyle.SQUARE:
        # Square grid
        grid_size = RADAR_RADIUS // 4
        for i in range(-4, 5):
            x = RADAR_CENTER[0] + i * grid_size
            pygame.draw.line(screen, colors["grid"], (x, RADAR_CENTER[1] - RADAR_RADIUS),
                           (x, RADAR_CENTER[1] + RADAR_RADIUS), 1)
            
        for i in range(-4, 5):
            y = RADAR_CENTER[1] + i * grid_size
            pygame.draw.line(screen, colors["grid"], (RADAR_CENTER[0] - RADAR_RADIUS, y),
                           (RADAR_CENTER[0] + RADAR_RADIUS, y), 1)
    
    elif appearance.grid_style == GridStyle.HEXAGONAL:
        # Hexagonal grid
        hex_radius = RADAR_RADIUS // 4
        for i in range(-2, 3):
            for j in range(-2, 3):
                center_x = RADAR_CENTER[0] + i * hex_radius * 1.5
                center_y = RADAR_CENTER[1] + j * hex_radius * math.sqrt(3)
                draw_hexagon(screen, (center_x, center_y), hex_radius, colors["grid"], 1)
    
    # Main radar circle
    pygame.draw.circle(screen, colors["grid"], RADAR_CENTER, RADAR_RADIUS, 2)
    
    # Range labels
    font_small = pygame.font.SysFont("Courier New", 12, bold=True)
    for i in range(1, 5):
        radius = (RADAR_RADIUS // 4) * i
        range_nm = i * range_settings.get_current_range_nm() // 4
        label = font_small.render(f"{range_nm}NM", True, colors["text"])
        screen.blit(label, (RADAR_CENTER[0] + radius + 5, RADAR_CENTER[1] - 10))
    
    # Draw heat map overlay if enabled
    if appearance.brightness < 0.8:
        draw_heat_map()
    
    # Draw measurement tools
    viz_tools.draw_measurement_tools(screen)
    
    # Draw scanlines effect if enabled
    if appearance.show_scanlines:
        draw_scanlines()
    
    # Draw CRT effect if enabled
    if appearance.crt_effect:
        draw_crt_effect()

def draw_hexagon(surface, center, radius, color, width):
    points = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        points.append((x, y))
    pygame.draw.polygon(surface, color, points, width)

def draw_heat_map():
    """Draw heat map overlay"""
    for x in range(heat_map.width):
        for y in range(heat_map.height):
            if heat_map.grid[x, y] > 0.1:
                # Convert grid coordinates to screen coordinates
                angle_rad = math.radians(x)
                distance = y * RADAR_RADIUS / heat_map.height
                
                screen_x = int(CENTER[0] + math.cos(angle_rad) * distance)
                screen_y = int(CENTER[1] + math.sin(angle_rad) * distance)
                
                # Draw with alpha based on intensity
                intensity = heat_map.grid[x, y]
                color = heat_map.get_color_at(x, y)
                alpha = int(100 * intensity * appearance.brightness)
                
                s = pygame.Surface((5, 5), pygame.SRCALPHA)
                pygame.draw.circle(s, (*color, alpha), (2, 2), 2)
                screen.blit(s, (screen_x-2, screen_y-2))
    
    heat_map.update()

def draw_scanlines():
    """Draw scanlines effect"""
    for y in range(0, HEIGHT, 2):
        s = pygame.Surface((WIDTH, 1), pygame.SRCALPHA)
        s.fill((0, 0, 0, 20))
        screen.blit(s, (0, y))

def draw_crt_effect():
    """Draw CRT monitor effect"""
    # Vignette effect
    s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    max_dist = math.sqrt(center_x**2 + center_y**2)
    
    for x in range(0, WIDTH, 10):
        for y in range(0, HEIGHT, 10):
            dist = math.sqrt((x-center_x)**2 + (y-center_y)**2) / max_dist
            alpha = int(50 * dist)
            s.fill((0, 0, 0, alpha), (x, y, 10, 10))
    
    screen.blit(s, (0, 0))
    
    # Screen curvature
    pygame.draw.ellipse(screen, (0, 0, 0, 30), 
                       (0, 0, WIDTH, HEIGHT), 10)

def draw_enhanced_sweep_line():
    config = ModeConfig.get_config(current_mode)
    colors = appearance.get_colors()
    sweep_color = colors["sweep"]
    
    if current_mode == DetectionMode.OMNI_360:
        # Pulsing circle
        pulse = int(50 + 50 * math.sin(pygame.time.get_ticks() / 200))
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(s, (*sweep_color, pulse), CENTER, RADAR_RADIUS, 1)
        screen.blit(s, (0, 0))
        
    elif current_mode == DetectionMode.NARROW_BEAM:
        # Focused beam with width
        beam_width = config["detection_arc"]
        start_angle = narrow_beam_angle - beam_width / 2
        end_angle = narrow_beam_angle + beam_width / 2
        
        # Draw beam area
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        points = [CENTER]
        for angle in np.linspace(start_angle, end_angle, 20):
            rad = math.radians(angle - 90)
            x = int(CENTER[0] + math.cos(rad) * RADAR_RADIUS)
            y = int(CENTER[1] + math.sin(rad) * RADAR_RADIUS)
            points.append((x, y))
        points.append(CENTER)
        
        pygame.draw.polygon(s, (*sweep_color, 30), points)
        screen.blit(s, (0, 0))
        
        # Draw center line
        rad = math.radians(narrow_beam_angle - 90)
        dest = (int(CENTER[0] + math.cos(rad) * RADAR_RADIUS),
               int(CENTER[1] + math.sin(rad) * RADAR_RADIUS))
        pygame.draw.line(screen, sweep_color, CENTER, dest, 3)
        
    else:
        # Sweep with selected style
        if appearance.sweep_style == SweepStyle.SOLID:
            rad = math.radians(sweep_angle)
            dest = (int(CENTER[0] + math.cos(rad) * RADAR_RADIUS),
                   int(CENTER[1] + math.sin(rad) * RADAR_RADIUS))
            pygame.draw.line(screen, sweep_color, CENTER, dest, 3)
            
        elif appearance.sweep_style == SweepStyle.DASHED:
            rad = math.radians(sweep_angle)
            for i in range(0, RADAR_RADIUS, 20):
                start = (int(CENTER[0] + math.cos(rad) * i),
                        int(CENTER[1] + math.sin(rad) * i))
                end = (int(CENTER[0] + math.cos(rad) * (i + 10)),
                      int(CENTER[1] + math.sin(rad) * (i + 10)))
                pygame.draw.line(screen, sweep_color, start, end, 3)
                
        elif appearance.sweep_style == SweepStyle.PULSING:
            pulse = int(150 + 100 * math.sin(pygame.time.get_ticks() / 100))
            rad = math.radians(sweep_angle)
            dest = (int(CENTER[0] + math.cos(rad) * RADAR_RADIUS),
                   int(CENTER[1] + math.sin(rad) * RADAR_RADIUS))
            
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.line(s, (*sweep_color, pulse), CENTER, dest, 3)
            screen.blit(s, (0, 0))
            
        elif appearance.sweep_style == SweepStyle.TRAIL:
            # Original trail effect
            for i in range(15):
                alpha = max(10, 255 - (i * 10))
                trail_angle = math.radians(sweep_angle - i * 2)
                tx = int(CENTER[0] + math.cos(trail_angle) * RADAR_RADIUS)
                ty = int(CENTER[1] + math.sin(trail_angle) * RADAR_RADIUS)
                
                s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                pygame.draw.line(s, (*sweep_color, alpha), CENTER, (tx, ty), 2)
                screen.blit(s, (0, 0))
    
    # Draw sonar pulse if active
    if current_mode == DetectionMode.ACTIVE_SONAR:
        time_since_pulse = pygame.time.get_ticks() - sonar_pulse_time
        if time_since_pulse < 2000:
            pulse_radius = int((time_since_pulse / 2000.0) * RADAR_RADIUS)
            pulse_alpha = int(255 * (1 - time_since_pulse / 2000.0))
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.circle(s, (*CYAN, pulse_alpha), CENTER, pulse_radius, 2)
            screen.blit(s, (0, 0))

def draw_enhanced_target(target: EnhancedTarget):
    pos = target.get_position()
    color = target.get_color()
    
    # Draw prediction path
    predictions = target.get_predicted_positions(5)
    if predictions:
        path_points = [pos]
        for pred_angle, pred_dist in predictions:
            angle_rad = math.radians(pred_angle - 90)
            px = int(CENTER[0] + math.cos(angle_rad) * pred_dist)
            py = int(CENTER[1] + math.sin(angle_rad) * pred_dist)
            path_points.append((px, py))
        
        if len(path_points) > 1:
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            # Draw with decreasing alpha for future predictions
            for i in range(len(path_points) - 1):
                alpha = max(30, target.alpha // (i + 1))
                pygame.draw.line(s, (*CYAN, alpha), 
                               path_points[i], path_points[i + 1], 1)
            screen.blit(s, (0, 0))
            
            # Draw prediction points
            for i, point in enumerate(path_points[1:], 1):
                alpha = max(30, target.alpha // (i + 1))
                s = pygame.Surface((6, 6), pygame.SRCALPHA)
                pygame.draw.circle(s, (*CYAN, alpha), (3, 3), 2)
                screen.blit(s, (point[0]-3, point[1]-3))
    
    # Draw history trail
    if len(target.position_history) > 1:
        trail_points = []
        for angle, dist, _ in list(target.position_history)[-20:]:
            angle_rad = math.radians(angle - 90)
            px = int(CENTER[0] + math.cos(angle_rad) * dist)
            py = int(CENTER[1] + math.sin(angle_rad) * dist)
            trail_points.append((px, py))
        
        if len(trail_points) > 1:
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            for i in range(len(trail_points) - 1):
                alpha = max(10, target.alpha // (len(trail_points) - i))
                pygame.draw.line(s, (*color[:3], alpha), 
                               trail_points[i], trail_points[i + 1], 1)
            screen.blit(s, (0, 0))
    
    # Draw velocity vector
    if target.velocity > 1.0:
        vel_length = min(target.velocity * 0.5, 50)
        vel_angle_rad = math.radians(target.velocity_angle)
        end_x = int(pos[0] + math.cos(vel_angle_rad) * vel_length)
        end_y = int(pos[1] + math.sin(vel_angle_rad) * vel_length)
        
        pygame.draw.line(screen, color[:3], pos, (end_x, end_y), 2)
        
        # Arrow head
        arrow_angle = math.radians(target.velocity_angle)
        arrow_size = 8
        left_x = end_x - arrow_size * math.cos(arrow_angle - 0.5)
        left_y = end_y - arrow_size * math.sin(arrow_angle - 0.5)
        right_x = end_x - arrow_size * math.cos(arrow_angle + 0.5)
        right_y = end_y - arrow_size * math.sin(arrow_angle + 0.5)
        pygame.draw.polygon(screen, color[:3], [(end_x, end_y), (left_x, left_y), (right_x, right_y)])
    
    # Draw target with selected icon
    draw_target_icon(target, pos, color)
    
    # Draw ID and classification
    font_tiny = pygame.font.SysFont("Courier New", 9, bold=True)
    id_text = f"T{target.id}"
    if target.is_ghost:
        id_text += " [G]"
    id_surf = font_tiny.render(id_text, True, color[:3])
    screen.blit(id_surf, (pos[0] + 12, pos[1] - 8))
    
    # Draw classification if close enough
    if target.distance < RADAR_RADIUS / 2:
        class_surf = font_tiny.render(target.classification[:8], True, CYAN)
        screen.blit(class_surf, (pos[0] - 20, pos[1] + 10))

def draw_target_icon(target: EnhancedTarget, pos: Tuple[int, int], color: Tuple):
    """Draw target with selected icon style"""
    size = max(6, min(15, int(target.intensity * 10)))
    
    if target.icon_type == "square":
        rect = pygame.Rect(pos[0]-size//2, pos[1]-size//2, size, size)
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(s, color, (0, 0, size, size))
        if target.selected:
            pygame.draw.rect(s, WHITE, (0, 0, size, size), 2)
        screen.blit(s, (pos[0]-size//2, pos[1]-size//2))
        
    elif target.icon_type == "triangle":
        points = [
            (pos[0], pos[1] - size),
            (pos[0] - size, pos[1] + size),
            (pos[0] + size, pos[1] + size)
        ]
        s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
        pygame.draw.polygon(s, color, points)
        if target.selected:
            pygame.draw.polygon(s, WHITE, points, 2)
        screen.blit(s, (pos[0]-size, pos[1]-size))
        
    elif target.icon_type == "diamond":
        points = [
            (pos[0], pos[1] - size),
            (pos[0] + size, pos[1]),
            (pos[0], pos[1] + size),
            (pos[0] - size, pos[1])
        ]
        s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
        pygame.draw.polygon(s, color, points)
        if target.selected:
            pygame.draw.polygon(s, WHITE, points, 2)
        screen.blit(s, (pos[0]-size, pos[1]-size))
        
    else:  # circle (default)
        s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
        if target.selected:
            pygame.draw.circle(s, WHITE, (size, size), size + 3, 2)
        pygame.draw.circle(s, color, (size, size), size)
        pygame.draw.circle(s, color, (size, size), size, 1)
        screen.blit(s, (pos[0]-size, pos[1]-size))

# New panel drawing functions
def draw_filters_panel(panel):
    """Draw filters and gain control panel"""
    font_title = pygame.font.SysFont("Courier New", 13, bold=True)
    font_data = pygame.font.SysFont("Courier New", 11, bold=True)
    
    panel.draw(screen)
    
    y = panel.rect.y + 30
    
    # Gain slider
    label = font_data.render("GAIN:", True, GREEN)
    screen.blit(label, (panel.rect.x + 10, y))
    
    # Draw slider track
    slider_x = panel.rect.x + 80
    slider_width = 150
    pygame.draw.rect(screen, DARK_GREEN, (slider_x, y, slider_width, 10))
    pygame.draw.rect(screen, GREEN, (slider_x, y, slider_width, 10), 1)
    
    # Draw slider thumb
    thumb_x = slider_x + int(audio_filters.gain * slider_width)
    pygame.draw.circle(screen, CYAN, (thumb_x, y + 5), 8)
    
    # Gain value
    value_text = font_data.render(f"{audio_filters.gain:.1f}x", True, CYAN)
    screen.blit(value_text, (slider_x + slider_width + 10, y - 2))
    
    y += 25
    
    # Noise gate threshold
    label = font_data.render("NOISE GATE:", True, GREEN)
    screen.blit(label, (panel.rect.x + 10, y))
    
    slider_x = panel.rect.x + 120
    thumb_x = slider_x + int(audio_filters.noise_gate_threshold * slider_width)
    pygame.draw.rect(screen, DARK_GREEN, (slider_x, y, slider_width, 10))
    pygame.draw.circle(screen, CYAN, (thumb_x, y + 5), 8)
    
    value_text = font_data.render(f"{audio_filters.noise_gate_threshold:.2f}", True, CYAN)
    screen.blit(value_text, (slider_x + slider_width + 10, y - 2))
    
    y += 25
    
    # Target size threshold
    label = font_data.render("MIN TARGET SIZE:", True, GREEN)
    screen.blit(label, (panel.rect.x + 10, y))
    
    slider_x = panel.rect.x + 140
    thumb_x = slider_x + int(audio_filters.target_size_threshold * slider_width)
    pygame.draw.rect(screen, DARK_GREEN, (slider_x, y, slider_width, 10))
    pygame.draw.circle(screen, CYAN, (thumb_x, y + 5), 8)
    
    value_text = font_data.render(f"{audio_filters.target_size_threshold:.1f}", True, CYAN)
    screen.blit(value_text, (slider_x + slider_width + 10, y - 2))

def draw_statistics_panel(panel):
    """Draw statistics panel"""
    font_title = pygame.font.SysFont("Courier New", 13, bold=True)
    font_data = pygame.font.SysFont("Courier New", 10, bold=True)
    
    panel.draw(screen)
    
    y = panel.rect.y + 30
    
    stats = target_manager.get_target_statistics()
    
    statistics = [
        ("TOTAL TARGETS:", f"{stats['total_targets']}"),
        ("ACTIVE TARGETS:", f"{stats['active_targets']}"),
        ("GHOST TARGETS:", f"{stats['ghost_targets']}"),
        ("HIGH THREATS:", f"{stats['threat_distribution']['HIGH']}"),
        ("MEDIUM THREATS:", f"{stats['threat_distribution']['MEDIUM']}"),
        ("LOW THREATS:", f"{stats['threat_distribution']['LOW']}"),
        ("AVG CONFIDENCE:", f"{stats['average_confidence']:.1%}"),
        ("MAX VELOCITY:", f"{stats['max_velocity']:.1f}"),
    ]
    
    for label, value in statistics:
        label_surf = font_data.render(label, True, GREEN)
        value_surf = font_data.render(value, True, CYAN)
        screen.blit(label_surf, (panel.rect.x + 10, y))
        screen.blit(value_surf, (panel.rect.x + 180, y))
        y += 18

def draw_recording_panel(panel):
    """Draw recording control panel"""
    font_title = pygame.font.SysFont("Courier New", 13, bold=True)
    font_data = pygame.font.SysFont("Courier New", 11, bold=True)
    
    panel.draw(screen)
    
    y = panel.rect.y + 30
    
    # Recording status
    status = "RECORDING" if recorder.is_recording else "STOPPED"
    status_color = RED if recorder.is_recording else GREEN
    
    status_label = font_data.render("STATUS:", True, GREEN)
    status_value = font_data.render(status, True, status_color)
    screen.blit(status_label, (panel.rect.x + 10, y))
    screen.blit(status_value, (panel.rect.x + 100, y))
    
    y += 25
    
    # Recording duration
    if recorder.current_session:
        duration = datetime.datetime.now() - recorder.current_session.start_time
        duration_str = str(duration).split('.')[0]
    else:
        duration_str = "00:00:00"
    
    duration_label = font_data.render("DURATION:", True, GREEN)
    duration_value = font_data.render(duration_str, True, CYAN)
    screen.blit(duration_label, (panel.rect.x + 10, y))
    screen.blit(duration_value, (panel.rect.x + 100, y))
    
    y += 25
    
    # Recorded targets
    target_count = len(recorder.current_session.targets) if recorder.current_session else 0
    target_label = font_data.render("TARGETS:", True, GREEN)
    target_value = font_data.render(str(target_count), True, CYAN)
    screen.blit(target_label, (panel.rect.x + 10, y))
    screen.blit(target_value, (panel.rect.x + 100, y))
    
    y += 30
    
    # Buttons (visual only - functionality in event handler)
    button_width = 120
    button_height = 25
    
    # Start/Stop button
    button_color = RED if recorder.is_recording else GREEN
    button_text = "STOP" if recorder.is_recording else "START"
    
    button_rect = pygame.Rect(panel.rect.x + 10, y, button_width, button_height)
    pygame.draw.rect(screen, button_color, button_rect)
    pygame.draw.rect(screen, WHITE, button_rect, 2)
    
    button_font = pygame.font.SysFont("Courier New", 10, bold=True)
    button_surf = button_font.render(button_text, True, WHITE)
    screen.blit(button_surf, (button_rect.x + 40, button_rect.y + 7))
    
    # Export button
    export_rect = pygame.Rect(panel.rect.x + 140, y, button_width, button_height)
    pygame.draw.rect(screen, BLUE, export_rect)
    pygame.draw.rect(screen, WHITE, export_rect, 2)
    
    export_surf = button_font.render("EXPORT CSV", True, WHITE)
    screen.blit(export_surf, (export_rect.x + 20, export_rect.y + 7))

def draw_appearance_controls():
    """Draw appearance controls in a small overlay"""
    font_small = pygame.font.SysFont("Courier New", 10, bold=True)
    
    # Theme selector
    y = HEIGHT - 100
    theme_label = font_small.render("THEME:", True, GREEN)
    screen.blit(theme_label, (WIDTH - 200, y))
    
    themes = ["GREEN", "BLUE", "AMBER", "RED"]
    theme_buttons = []
    
    for i, theme in enumerate(themes):
        button_rect = pygame.Rect(WIDTH - 140 + i*40, y, 35, 20)
        theme_buttons.append((button_rect, theme))
        
        # Draw button
        is_active = appearance.color_theme.name == theme
        color = GREEN if is_active else DARK_GREEN
        pygame.draw.rect(screen, color, button_rect)
        pygame.draw.rect(screen, WHITE if is_active else GRAY, button_rect, 1)
        
        # Draw theme color preview
        preview_rect = pygame.Rect(button_rect.x + 5, button_rect.y + 5, 25, 10)
        if theme == "GREEN":
            pygame.draw.rect(screen, GREEN, preview_rect)
        elif theme == "BLUE":
            pygame.draw.rect(screen, BLUE, preview_rect)
        elif theme == "AMBER":
            pygame.draw.rect(screen, AMBER, preview_rect)
        elif theme == "RED":
            pygame.draw.rect(screen, RED, preview_rect)
    
    y += 30
    
    # Brightness control
    brightness_label = font_small.render("BRIGHTNESS:", True, GREEN)
    screen.blit(brightness_label, (WIDTH - 200, y))
    
    # Brightness slider
    slider_x = WIDTH - 120
    slider_width = 100
    pygame.draw.rect(screen, DARK_GREEN, (slider_x, y, slider_width, 10))
    pygame.draw.rect(screen, GREEN, (slider_x, y, slider_width, 10), 1)
    
    thumb_x = slider_x + int(appearance.brightness * slider_width)
    pygame.draw.circle(screen, CYAN, (thumb_x, y + 5), 8)
    
    # Brightness value
    value_text = font_small.render(f"{appearance.brightness:.1f}", True, CYAN)
    screen.blit(value_text, (slider_x + slider_width + 10, y - 2))
    
    return theme_buttons

# Main function with enhanced controls
def main():
    global sweep_angle, current_mode, narrow_beam_angle, dragged_panel
    global WIDTH, HEIGHT, CENTER, RADAR_CENTER, screen 
    
    # State variables
    is_paused = False
    is_fullscreen = False
    measurement_start = None
    right_click_menu = None
    mouse_wheel_zoom = 0
    
    # Slider interaction state
    active_slider = None
    slider_value_start = None
    
    try:
        if stream:
            stream.start()
            print("Audio stream started")
    except Exception as e:
        print(f"Could not start audio stream: {e}")
        
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.KEYDOWN:
                # Mode switching
                if event.key == pygame.K_1:
                    current_mode = DetectionMode.PASSIVE
                elif event.key == pygame.K_2:
                    current_mode = DetectionMode.ACTIVE_SONAR
                elif event.key == pygame.K_3:
                    current_mode = DetectionMode.WIDE_BEAM
                elif event.key == pygame.K_4:
                    current_mode = DetectionMode.NARROW_BEAM
                elif event.key == pygame.K_5:
                    current_mode = DetectionMode.OMNI_360
                    
                # Control keys
                elif event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    if current_mode == DetectionMode.ACTIVE_SONAR:
                        send_sonar_pulse()
                elif event.key == pygame.K_LEFT:
                    narrow_beam_angle = (narrow_beam_angle - 5) % 360
                elif event.key == pygame.K_RIGHT:
                    narrow_beam_angle = (narrow_beam_angle + 5) % 360
                elif event.key == pygame.K_p:
                    is_paused = not is_paused
                elif event.key == pygame.K_r:
                    # Reset display
                    target_manager.targets.clear()
                    heat_map.grid.fill(0)
                    viz_tools.clear_measurements()
                elif event.key == pygame.K_s:
                    # Screenshot
                    ScreenCapture.capture_screen()
                elif event.key == pygame.K_f:
                    # Toggle fullscreen - FIXED
                    is_fullscreen = not is_fullscreen
                    if is_fullscreen:
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                elif event.key == pygame.K_m:
                    # Toggle mini-map
                    viz_tools.mini_map_visible = not viz_tools.mini_map_visible
                elif event.key == pygame.K_c:
                    # Toggle compass
                    viz_tools.compass_visible = not viz_tools.compass_visible
                elif event.key == pygame.K_g:
                    # Toggle grid
                    appearance.grid_style = GridStyle.CIRCULAR if appearance.grid_style != GridStyle.CIRCULAR else GridStyle.SQUARE
                elif event.key == pygame.K_t:
                    # Cycle through themes
                    themes = list(ColorTheme)
                    current_index = themes.index(appearance.color_theme)
                    appearance.color_theme = themes[(current_index + 1) % len(themes)]
                elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    range_settings.zoom_in()
                elif event.key == pygame.K_MINUS:
                    range_settings.zoom_out()

                        
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        panel_clicked = False
                        
                        # Check panel interactions first
                        for panel in panels:
                            if panel.handle_event(event):
                                panel_clicked = True
                                dragged_panel = panel
                                break
                        
                        # Check appearance controls
                        theme_buttons = draw_appearance_controls()
                        for button_rect, theme in theme_buttons:
                            if button_rect.collidepoint(event.pos):
                                appearance.color_theme = ColorTheme[theme]
                                panel_clicked = True
                                break
                        
                        # Check slider interactions
                        if not panel_clicked:
                            # Check gain slider
                            panel = panels[5]  # Filters panel
                            slider_x = panel.rect.x + 80
                            slider_y = panel.rect.y + 30
                            slider_width = 150
                            
                            slider_rect = pygame.Rect(slider_x, slider_y - 5, slider_width, 20)
                            if slider_rect.collidepoint(event.pos):
                                active_slider = "gain"
                                slider_value_start = audio_filters.gain
                                panel_clicked = True
                        
                        # If not clicking on UI, handle radar interactions
                        if not panel_clicked:
                            # Start measurement if Ctrl is held
                            if pygame.key.get_mods() & pygame.KMOD_CTRL:
                                measurement_start = mouse_pos
                            else:
                                # Select target
                                target_manager.select_target_at(event.pos)
                                
                    elif event.button == 3:  # Right click
                        # Open context menu
                        right_click_menu = mouse_pos
                        
                    elif event.button == 4:  # Scroll up
                        range_settings.zoom_in()
                        
                    elif event.button == 5:  # Scroll down
                        range_settings.zoom_out()
                        
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:  # Left click release
                        for panel in panels:
                            panel.handle_event(event)
                        dragged_panel = None
                        active_slider = None
                        
                        # Complete measurement if started
                        if measurement_start:
                            viz_tools.add_measurement_line(measurement_start, mouse_pos)
                            measurement_start = None
                            
                    elif event.button == 3:  # Right click release
                        right_click_menu = None
                        
                elif event.type == pygame.MOUSEMOTION:
                    # Handle panel dragging
                    for panel in panels:
                        panel.handle_event(event)
                    
                    # Handle slider dragging
                    if active_slider == "gain":
                        panel = panels[5]  # Filters panel
                        slider_x = panel.rect.x + 80
                        slider_width = 150
                        
                        # Calculate new gain value
                        mouse_x = event.pos[0]
                        relative_x = max(0, min(slider_width, mouse_x - slider_x))
                        audio_filters.gain = relative_x / slider_width * 3.0  # 0-3x range
                    
                    # Update measurement line preview
                    if measurement_start:
                        pass  # Line will be drawn in main drawing loop
                        
                elif event.type == pygame.VIDEORESIZE:
                    WIDTH, HEIGHT = event.w, event.h
                    CENTER = (450, HEIGHT // 2)
                    RADAR_CENTER = (450, HEIGHT // 2)
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            
            # Draw everything
            draw_enhanced_radar_background()
            
            if not is_paused:
                draw_enhanced_sweep_line()
                
                # Update targets based on mode
                config = ModeConfig.get_config(current_mode)
                
                if current_noise_data["intensity"] > audio_filters.noise_gate_threshold and current_noise_data["detected_sounds"]:
                    detected_angle = math.degrees(current_noise_data["angle"])
                    
                    # Apply mode-specific detection logic
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
                        
                        target_manager.update_or_create(
                            detected_angle,
                            dist,
                            current_noise_data["intensity"],
                            types,
                            current_noise_data["primary_threat"],
                            current_mode
                        )
                
                target_manager.update_all()
                
                # Update sweep angle if not paused
                if config["sweep_speed"] > 0:
                    sweep_angle = (sweep_angle + config["sweep_speed"]) % 360
            
            # Draw all targets
            for target in target_manager.targets.values():
                draw_enhanced_target(target)
            
            # Draw visualization tools
            viz_tools.draw_compass(screen)
            viz_tools.draw_mini_map(screen)
            
            # Draw measurement preview
            if measurement_start:
                pygame.draw.line(screen, CYAN, measurement_start, mouse_pos, 2)
                
                # Draw distance preview
                dx = mouse_pos[0] - measurement_start[0]
                dy = mouse_pos[1] - measurement_start[1]
                distance_pixels = math.sqrt(dx**2 + dy**2)
                distance_nm = distance_pixels / range_settings.get_pixels_per_nm()
                
                font = pygame.font.SysFont("Courier New", 10, bold=True)
                text = font.render(f"{distance_nm:.1f} NM", True, CYAN)
                screen.blit(text, (mouse_pos[0] + 5, mouse_pos[1] + 5))
            
            # Draw UI panels
            draw_mode_selector(panels[0])
            draw_system_status(panels[1])
            draw_own_ship_data(panels[2])
            draw_tracked_targets(panels[3])
            draw_acoustic_sensor(panels[4])
            draw_filters_panel(panels[5])
            draw_statistics_panel(panels[6])
            draw_recording_panel(panels[7])
            
            # Draw appearance controls
            draw_appearance_controls()
            
            # Draw right-click menu
            if right_click_menu:
                menu_rect = pygame.Rect(right_click_menu[0], right_click_menu[1], 150, 100)
                pygame.draw.rect(screen, (30, 30, 30), menu_rect)
                pygame.draw.rect(screen, GREEN, menu_rect, 2)
                
                font = pygame.font.SysFont("Courier New", 10, bold=True)
                options = ["Clear Measurements", "Take Screenshot", "Toggle Grid", "Reset Display"]
                
                for i, option in enumerate(options):
                    text = font.render(option, True, WHITE)
                    screen.blit(text, (right_click_menu[0] + 10, right_click_menu[1] + 10 + i*20))
            
            # Draw pause indicator
            if is_paused:
                font = pygame.font.SysFont("Courier New", 24, bold=True)
                pause_text = font.render("PAUSED", True, RED)
                text_rect = pause_text.get_rect(center=(WIDTH//2, 30))
                screen.blit(pause_text, text_rect)
            
            # Draw zoom level
            if range_settings.zoom_level != 1.0:
                font = pygame.font.SysFont("Courier New", 12, bold=True)
                zoom_text = font.render(f"ZOOM: {range_settings.zoom_level:.1f}x", True, CYAN)
                screen.blit(zoom_text, (WIDTH - 150, 30))
            
            # Draw instructions
            font_inst = pygame.font.SysFont("Courier New", 10, bold=True)
            instructions = [
                "Drag panels to move, corners to resize",
                "Ctrl+Click: Measure distance | Scroll: Zoom",
                "1-5: Modes | Space: Sonar pulse | P: Pause",
                "S: Screenshot | F: Fullscreen | R: Reset"
            ]
            
            for i, line in enumerate(instructions):
                inst_text = font_inst.render(line, True, GRAY)
                screen.blit(inst_text, (10, HEIGHT - 80 + i*15))
            
            pygame.display.flip()
            clock.tick(FPS)
    
    pygame.quit()

if __name__ == "__main__":
    main()