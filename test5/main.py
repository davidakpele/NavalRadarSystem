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

WIDTH, HEIGHT = 1600, 900
CENTER = (450, HEIGHT // 2)  
RADAR_RADIUS = 350 
RADAR_CENTER = (450, HEIGHT // 2)  
FPS = 60
FS = 44100 
CHANNELS = 2
CHUNK = 1024 

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Naval Acoustic Radar - Multi-Mode Detection System")
clock = pygame.time.Clock()

# Colors
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

# Draggable panel system
class DraggablePanel:
    def __init__(self, x, y, width, height, title="Panel", color=BLACK, border_color=GREEN):
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.color = color
        self.border_color = border_color
        self.dragging = False
        self.drag_offset = (0, 0)
        self.visible = True
        
    def handle_event(self, event):
        if not self.visible:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                title_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 25)
                if title_rect.collidepoint(event.pos):
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
                # Keep panel within screen bounds
                self.rect.x = max(0, min(self.rect.x, WIDTH - self.rect.width))
                self.rect.y = max(0, min(self.rect.y, HEIGHT - self.rect.height))
                return True
                
        return False
        
    def draw(self, screen):
        if not self.visible:
            return
            
        # Draw panel background
        pygame.draw.rect(screen, self.color, self.rect)
        
        # Draw title bar
        title_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 25)
        pygame.draw.rect(screen, DARK_GREEN, title_rect)
        pygame.draw.rect(screen, self.border_color, title_rect, 1)
        
        # Draw title
        font_title = pygame.font.SysFont("Courier New", 13, bold=True)
        title_text = font_title.render(self.title, True, CYAN)
        screen.blit(title_text, (self.rect.x + 10, self.rect.y + 5))
        
        # Draw panel border
        pygame.draw.rect(screen, self.border_color, self.rect, 2)
        
        return title_rect

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
                "color": GREEN,
                "shows_true_distance": False
            },
            DetectionMode.ACTIVE_SONAR: {
                "name": "ACTIVE SONAR",
                "description": "Pulse echo ranging",
                "detection_arc": 45,
                "range_multiplier": 2.0,
                "accuracy": 0.95,
                "sweep_speed": 2,
                "color": CYAN,
                "shows_true_distance": True
            },
            DetectionMode.WIDE_BEAM: {
                "name": "WIDE BEAM",
                "description": "Broad coverage",
                "detection_arc": 120,
                "range_multiplier": 0.7,
                "accuracy": 0.4,
                "sweep_speed": 4,
                "color": YELLOW,
                "shows_true_distance": False
            },
            DetectionMode.NARROW_BEAM: {
                "name": "NARROW BEAM",
                "description": "Focused sector",
                "detection_arc": 30,
                "range_multiplier": 1.5,
                "accuracy": 0.9,
                "sweep_speed": 1,
                "color": ORANGE,
                "shows_true_distance": False
            },
            DetectionMode.OMNI_360: {
                "name": "360° OMNI",
                "description": "All directions",
                "detection_arc": 360,
                "range_multiplier": 0.5,
                "accuracy": 0.3,
                "sweep_speed": 0,  
                "color": BLUE,
                "shows_true_distance": False
            }
        }
        return configs.get(mode, configs[DetectionMode.PASSIVE])

class Target:
    """Advanced target with mode-specific properties"""
    next_id = 1
    
    def __init__(self, angle, distance, intensity, sound_types, threat_level, detection_mode):
        self.id = Target.next_id
        Target.next_id += 1
        
        self.angle = angle
        self.distance = distance
        self.intensity = intensity
        self.sound_types = sound_types
        self.threat_level = threat_level
        self.detection_mode = detection_mode
        
        # Position tracking
        self.position_history = deque(maxlen=50)
        self.position_history.append((angle, distance, pygame.time.get_ticks()))
        
        # Velocity
        self.velocity = 0.0
        self.velocity_angle = 0.0
        self.angular_velocity = 0.0
        
        # Prediction
        self.predicted_positions = []
        
        # Display
        self.alpha = 255
        self.last_update = pygame.time.get_ticks()
        self.is_ghost = False
        self.ghost_start_time = 0
        self.selected = False
        
        # Mode-specific accuracy
        config = ModeConfig.get_config(detection_mode)
        self.accuracy = config["accuracy"]
        
        # Track data
        self.track_data = []
        self.track_data.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "angle": angle,
            "distance": distance,
            "intensity": intensity,
            "sound_types": sound_types,
            "threat_level": threat_level,
            "detection_mode": detection_mode
        })
    
    def update(self, angle, distance, intensity, sound_types, threat_level, detection_mode):
        current_time = pygame.time.get_ticks()
        
        self.position_history.append((angle, distance, current_time))
        
        if len(self.position_history) >= 2:
            self._calculate_velocity()
        
        self._update_prediction()
        
        self.angle = angle
        self.distance = distance
        self.intensity = intensity
        self.sound_types = sound_types
        self.threat_level = threat_level
        self.detection_mode = detection_mode
        self.alpha = 255
        self.last_update = current_time
        self.is_ghost = False
        
        config = ModeConfig.get_config(detection_mode)
        self.accuracy = config["accuracy"]
        
        self.track_data.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "angle": angle,
            "distance": distance,
            "intensity": intensity,
            "sound_types": sound_types,
            "threat_level": threat_level,
            "velocity": self.velocity,
            "velocity_angle": self.velocity_angle,
            "detection_mode": detection_mode
        })
    
    def _calculate_velocity(self):
        if len(self.position_history) < 2:
            return
        
        (angle1, dist1, time1) = self.position_history[-2]
        (angle2, dist2, time2) = self.position_history[-1]
        
        time_delta = (time2 - time1) / 1000.0
        
        if time_delta > 0:
            x1 = dist1 * math.cos(math.radians(angle1))
            y1 = dist1 * math.sin(math.radians(angle1))
            x2 = dist2 * math.cos(math.radians(angle2))
            y2 = dist2 * math.sin(math.radians(angle2))
            
            vx = (x2 - x1) / time_delta
            vy = (y2 - y1) / time_delta
            
            self.velocity = math.sqrt(vx**2 + vy**2)
            self.velocity_angle = math.degrees(math.atan2(vy, vx))
            
            angle_change = angle2 - angle1
            if angle_change > 180:
                angle_change -= 360
            elif angle_change < -180:
                angle_change += 360
            self.angular_velocity = angle_change / time_delta
    
    def _update_prediction(self):
        self.predicted_positions = []
        
        if self.velocity > 1.0:
            for t in range(1, 6):
                x = self.distance * math.cos(math.radians(self.angle))
                y = self.distance * math.sin(math.radians(self.angle))
                
                vx = self.velocity * math.cos(math.radians(self.velocity_angle))
                vy = self.velocity * math.sin(math.radians(self.velocity_angle))
                
                pred_x = x + vx * t
                pred_y = y + vy * t
                
                pred_dist = math.sqrt(pred_x**2 + pred_y**2)
                pred_angle = math.degrees(math.atan2(pred_y, pred_x))
                
                self.predicted_positions.append((pred_angle, pred_dist))
    
    def fade(self):
        time_since_update = pygame.time.get_ticks() - self.last_update
        
        if time_since_update > 500 and not self.is_ghost:
            self.is_ghost = True
            self.ghost_start_time = pygame.time.get_ticks()
        
        if self.is_ghost:
            ghost_duration = pygame.time.get_ticks() - self.ghost_start_time
            if ghost_duration < 5000:
                self.alpha = max(50, 255 - int((ghost_duration / 5000.0) * 205))
                return True
            else:
                return False
        
        if time_since_update > 100:
            self.alpha = max(0, self.alpha - 2)
        
        return self.alpha > 0
    
    def get_position(self):
        angle_rad = math.radians(self.angle - 90)
        px = int(CENTER[0] + math.cos(angle_rad) * self.distance)
        py = int(CENTER[1] + math.sin(angle_rad) * self.distance)
        return (px, py)
    
    def get_color(self):
        if self.is_ghost:
            return (150, 150, 150)
        elif self.selected:
            return WHITE
        elif self.threat_level == "FRIENDLY":
            return GREEN
        elif self.threat_level == "THREAT":
            return RED
        else:
            return YELLOW
    
    def get_range_nm(self):
        """Convert pixel distance to nautical miles (approximate)"""
        return self.distance / 17.5  # Calibration factor

class TargetManager:
    def __init__(self):
        self.targets = {}
        self.selected_target = None
        self.collision_warnings = []
    
    def update_or_create(self, angle, distance, intensity, sound_types, threat_level, detection_mode):
        config = ModeConfig.get_config(detection_mode)
        detection_arc = config["detection_arc"]
        
        found_target = None
        for tid, target in self.targets.items():
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
            new_target = Target(angle, distance, intensity, sound_types, threat_level, detection_mode)
            self.targets[new_target.id] = new_target
    
    def update_all(self):
        to_remove = []
        for tid, target in self.targets.items():
            if not target.fade():
                to_remove.append(tid)
        
        for tid in to_remove:
            del self.targets[tid]
    
    def check_collisions(self):
        self.collision_warnings = []
        target_list = list(self.targets.values())
        for i, target1 in enumerate(target_list):
            for target2 in target_list[i+1:]:
                if self._check_collision_pair(target1, target2):
                    self.collision_warnings.append((target1.id, target2.id))
    
    def _check_collision_pair(self, target1, target2):
        if not target1.predicted_positions or not target2.predicted_positions:
            return False
        
        for (angle1, dist1) in target1.predicted_positions:
            for (angle2, dist2) in target2.predicted_positions:
                x1 = dist1 * math.cos(math.radians(angle1))
                y1 = dist1 * math.sin(math.radians(angle1))
                x2 = dist2 * math.cos(math.radians(angle2))
                y2 = dist2 * math.sin(math.radians(angle2))
                
                distance = math.sqrt((x2-x1)**2 + (y2-y1)**2)
                if distance < 50:
                    return True
        
        return False
    
    def select_target_at(self, pos):
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

target_manager = TargetManager()

# Create draggable panels
panels = [
    DraggablePanel(500, 10, 280, 220, "DETECTION MODE", BLACK, GREEN),
    DraggablePanel(500, 240, 280, 140, "SYSTEM STATUS", BLACK, GREEN),
    DraggablePanel(500, 390, 280, 140, "OWN SHIP DATA", BLACK, GREEN),
    DraggablePanel(500, 540, 280, 350, "TRACKED TARGETS", BLACK, GREEN),
    DraggablePanel(WIDTH - 320, 10, 310, 120, "ACOUSTIC SENSOR", BLACK, GREEN),
]

# Variable to store which panel is currently being dragged
dragged_panel = None

class MultiSoundClassifier:
    @staticmethod
    def analyze_audio(audio_data, sample_rate):
        try:
            fft_data = np.fft.rfft(audio_data)
            fft_freq = np.fft.rfftfreq(len(audio_data), 1/sample_rate)
            magnitude = np.abs(fft_data)
            
            dominant_idx = np.argmax(magnitude[1:]) + 1
            dominant_freq = fft_freq[dominant_idx]
            
            top_indices = np.argsort(magnitude)[-10:]
            top_freqs = fft_freq[top_indices]
            
            return dominant_freq, top_freqs, magnitude, fft_freq
        except:
            return 0.0, [], [], []
    
    @staticmethod
    def detect_multiple_sounds(dominant_freq, magnitude, fft_freq, intensity):
        if len(magnitude) == 0 or len(fft_freq) == 0:
            return [], "NEUTRAL", 0.0
        
        detected_sounds = []
        
        spectral_centroid = np.sum(fft_freq * magnitude) / (np.sum(magnitude) + 1e-10)
        spectral_bandwidth = np.sqrt(np.sum(((fft_freq - spectral_centroid) ** 2) * magnitude) / (np.sum(magnitude) + 1e-10))
        
        low_energy = np.sum(magnitude[(fft_freq >= 20) & (fft_freq < 250)])
        mid_energy = np.sum(magnitude[(fft_freq >= 250) & (fft_freq < 2000)])
        high_energy = np.sum(magnitude[(fft_freq >= 2000) & (fft_freq < 8000)])
        total_energy = low_energy + mid_energy + high_energy + 1e-10
        
        low_ratio = low_energy / total_energy
        mid_ratio = mid_energy / total_energy
        high_ratio = high_energy / total_energy
        
        peaks, _ = signal.find_peaks(magnitude, height=np.max(magnitude) * 0.15, distance=20)
        peak_freqs = fft_freq[peaks]
        
        harmonics_detected = 0
        if len(peak_freqs) > 0:
            base_freq = peak_freqs[0]
            for freq in peak_freqs[1:]:
                ratio = freq / (base_freq + 1e-10)
                if 1.8 < ratio < 2.2 or 2.8 < ratio < 3.2:
                    harmonics_detected += 1
        
        if (harmonics_detected >= 2 or 
            (mid_ratio > 0.25 and high_ratio > 0.15 and spectral_bandwidth > 400)):
            confidence = min(0.92, 0.55 + (harmonics_detected * 0.1) + (mid_ratio * 0.3))
            detected_sounds.append({"type": "MUSIC", "confidence": confidence, "threat": "FRIENDLY"})
        
        voice_energy = np.sum(magnitude[(fft_freq >= 85) & (fft_freq < 300)])
        if voice_energy / (total_energy + 1e-10) > 0.15:
            confidence = min(0.88, 0.5 + (voice_energy / total_energy))
            detected_sounds.append({"type": "VOICE", "confidence": confidence, "threat": "FRIENDLY" if intensity < 0.7 else "NEUTRAL"})
        
        if high_ratio > 0.3 and spectral_bandwidth > 1000 and intensity > 0.5:
            confidence = min(0.85, 0.5 + high_ratio * 0.6)
            detected_sounds.append({"type": "IMPACT", "confidence": confidence, "threat": "NEUTRAL" if intensity < 0.9 else "THREAT"})
        
        if any(s["threat"] == "THREAT" for s in detected_sounds):
            primary_threat = "THREAT"
        elif any(s["threat"] == "NEUTRAL" for s in detected_sounds):
            primary_threat = "NEUTRAL"
        elif any(s["threat"] == "FRIENDLY" for s in detected_sounds):
            primary_threat = "FRIENDLY"
        else:
            primary_threat = "NEUTRAL"
        
        avg_confidence = np.mean([s["confidence"] for s in detected_sounds]) if detected_sounds else 0.3
        
        return detected_sounds, primary_threat, avg_confidence

def send_sonar_pulse():
    """Send active sonar pulse"""
    global sonar_pulse_time, sonar_echo_targets
    sonar_pulse_time = pygame.time.get_ticks()
    sonar_echo_targets = []

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

def draw_radar_background():
    screen.fill(BLACK)
    
    config = ModeConfig.get_config(current_mode)
    mode_color = config["color"]
    
    radar_rect = pygame.Rect(RADAR_CENTER[0] - RADAR_RADIUS - 50, 
                             RADAR_CENTER[1] - RADAR_RADIUS - 50,
                             (RADAR_RADIUS + 50) * 2, 
                             (RADAR_RADIUS + 50) * 2)
    pygame.draw.rect(screen, BLACK, radar_rect)
    pygame.draw.rect(screen, GREEN, radar_rect, 2)
    
    # Concentric circles
    for i in range(1, 5):
        pygame.draw.circle(screen, DARK_GREEN, RADAR_CENTER, (RADAR_RADIUS // 4) * i, 1)
    
    # Main circle
    pygame.draw.circle(screen, GREEN, RADAR_CENTER, RADAR_RADIUS, 2)
    
    # Radial lines
    for i in range(0, 360, 30):
        rad = math.radians(i)
        dest = (int(RADAR_CENTER[0] + math.cos(rad) * RADAR_RADIUS), 
                int(RADAR_CENTER[1] + math.sin(rad) * RADAR_RADIUS))
        pygame.draw.line(screen, DARK_GREEN, RADAR_CENTER, dest, 1)
    
    # Range rings labels
    font_small = pygame.font.SysFont("Courier New", 12, bold=True)
    for i in range(1, 5):
        radius = (RADAR_RADIUS // 4) * i
        range_nm = i * 5  # 5 NM per ring
        label = font_small.render(f"{range_nm}NM", True, DARK_GREEN)
        screen.blit(label, (RADAR_CENTER[0] + radius + 5, RADAR_CENTER[1] - 10))
        
    # Draw detection arc based on mode
    if current_mode == DetectionMode.NARROW_BEAM:
        # Draw narrow beam cone
        beam_width = config["detection_arc"]
        start_angle = narrow_beam_angle - beam_width / 2
        end_angle = narrow_beam_angle + beam_width / 2
        
        for angle in [start_angle, end_angle]:
            rad = math.radians(angle - 90)
            dest = (int(CENTER[0] + math.cos(rad) * RADAR_RADIUS),
                   int(CENTER[1] + math.sin(rad) * RADAR_RADIUS))
            pygame.draw.line(screen, mode_color, CENTER, dest, 2)
    
    elif current_mode == DetectionMode.WIDE_BEAM:
        # Draw wide beam arc
        beam_width = config["detection_arc"]
        start_angle = sweep_angle - beam_width / 2
        end_angle = sweep_angle + beam_width / 2
        
        for angle in [start_angle, end_angle]:
            rad = math.radians(angle - 90)
            dest = (int(CENTER[0] + math.cos(rad) * RADAR_RADIUS),
                   int(CENTER[1] + math.sin(rad) * RADAR_RADIUS))
            pygame.draw.line(screen, mode_color, CENTER, dest, 2)
    
    # Draw sonar pulse rings if active
    if current_mode == DetectionMode.ACTIVE_SONAR:
        time_since_pulse = pygame.time.get_ticks() - sonar_pulse_time
        if time_since_pulse < 2000:  
            # Expanding ring
            pulse_radius = int((time_since_pulse / 2000.0) * RADAR_RADIUS)
            pulse_alpha = int(255 * (1 - time_since_pulse / 2000.0))
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.circle(s, (*CYAN, pulse_alpha), CENTER, pulse_radius, 2)
            screen.blit(s, (0, 0))

def draw_sweep_line():
    config = ModeConfig.get_config(current_mode)
    mode_color = config["color"]
    
    if current_mode == DetectionMode.OMNI_360:
        # No sweep line for omni mode - draw pulsing circle instead
        pulse = int(50 + 50 * math.sin(pygame.time.get_ticks() / 200))
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(s, (*mode_color, pulse), CENTER, RADAR_RADIUS, 1)
        screen.blit(s, (0, 0))
    elif current_mode == DetectionMode.NARROW_BEAM:
        # Draw beam line at fixed angle
        rad = math.radians(narrow_beam_angle - 90)
        dest = (int(CENTER[0] + math.cos(rad) * RADAR_RADIUS),
               int(CENTER[1] + math.sin(rad) * RADAR_RADIUS))
        pygame.draw.line(screen, mode_color, CENTER, dest, 3)
    else:
        # Normal sweep with trail
        for i in range(15):
            alpha = max(10, 255 - (i * 10))
            trail_angle = math.radians(sweep_angle - i * 2)
            tx = int(CENTER[0] + math.cos(trail_angle) * RADAR_RADIUS)
            ty = int(CENTER[1] + math.sin(trail_angle) * RADAR_RADIUS)
            
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.line(s, (0, 255, 65, alpha), RADAR_CENTER, (tx, ty), 2)
            screen.blit(s, (0,0))

def draw_target(target):
    pos = target.get_position()
    color = target.get_color()
    
    # Draw prediction path
    if target.predicted_positions:
        path_points = [pos]
        for (pred_angle, pred_dist) in target.predicted_positions:
            angle_rad = math.radians(pred_angle - 90)
            px = int(CENTER[0] + math.cos(angle_rad) * pred_dist)
            py = int(CENTER[1] + math.sin(angle_rad) * pred_dist)
            path_points.append((px, py))
        
        if len(path_points) > 1:
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.lines(s, (*CYAN, target.alpha // 3), False, path_points, 1)
            screen.blit(s, (0, 0))
            
            for point in path_points[1:]:
                pygame.draw.circle(screen, (*CYAN, target.alpha // 2), point, 2)
    
    # Draw history trail
    if len(target.position_history) > 1:
        trail_points = []
        for (angle, dist, _) in list(target.position_history)[-10:]:
            angle_rad = math.radians(angle - 90)
            px = int(CENTER[0] + math.cos(angle_rad) * dist)
            py = int(CENTER[1] + math.sin(angle_rad) * dist)
            trail_points.append((px, py))
        
        if len(trail_points) > 1:
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.lines(s, (*color, target.alpha // 4), False, trail_points, 1)
            screen.blit(s, (0, 0))
    
    # Draw velocity vector
    if target.velocity > 1.0:
        vel_length = min(target.velocity * 0.5, 50)
        vel_angle_rad = math.radians(target.velocity_angle)
        end_x = int(pos[0] + math.cos(vel_angle_rad) * vel_length)
        end_y = int(pos[1] + math.sin(vel_angle_rad) * vel_length)
        
        pygame.draw.line(screen, color, pos, (end_x, end_y), 2)
        
        arrow_angle = math.radians(target.velocity_angle)
        arrow_size = 8
        left_x = end_x - arrow_size * math.cos(arrow_angle - 0.5)
        left_y = end_y - arrow_size * math.sin(arrow_angle - 0.5)
        right_x = end_x - arrow_size * math.cos(arrow_angle + 0.5)
        right_y = end_y - arrow_size * math.sin(arrow_angle + 0.5)
        pygame.draw.polygon(screen, color, [(end_x, end_y), (left_x, left_y), (right_x, right_y)])
    
    # Draw target blip
    if target.is_ghost:
        s = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, target.alpha), (10, 10), 8, 2)
        pygame.draw.line(s, (*color, target.alpha), (5, 10), (15, 10), 1)
        pygame.draw.line(s, (*color, target.alpha), (10, 5), (10, 15), 1)
        screen.blit(s, (pos[0]-10, pos[1]-10))
    else:
        s = pygame.Surface((18, 18), pygame.SRCALPHA)
        if target.selected:
            pygame.draw.circle(s, (*color, target.alpha), (9, 9), 10, 3)
        pygame.draw.circle(s, (*color, target.alpha), (9, 9), 7)
        pygame.draw.circle(s, (*color, target.alpha), (9, 9), 7, 2)
        screen.blit(s, (pos[0]-9, pos[1]-9))
    
    # Draw ID
    font_tiny = pygame.font.SysFont("Courier New", 9, bold=True)
    id_text = f"T{target.id}"
    if target.is_ghost:
        id_text += " [G]"
    id_surf = font_tiny.render(id_text, True, color)
    screen.blit(id_surf, (pos[0] + 12, pos[1] - 8))

def draw_mode_selector(panel):
    """Draw mode selection panel"""
    font_title = pygame.font.SysFont("Courier New", 13, bold=True)
    font_mode = pygame.font.SysFont("Courier New", 10, bold=True)
    
    # Draw the panel background
    title_rect = panel.draw(screen)
    
    # Draw content inside panel
    y = panel.rect.y + 30
    
    modes = [
        (DetectionMode.PASSIVE, "1"),
        (DetectionMode.ACTIVE_SONAR, "2"),
        (DetectionMode.WIDE_BEAM, "3"),
        (DetectionMode.NARROW_BEAM, "4"),
        (DetectionMode.OMNI_360, "5")
    ]
    
    for mode, key in modes:
        config = ModeConfig.get_config(mode)
        is_current = (mode == current_mode)
        
        # Mode indicator
        if is_current:
            pygame.draw.rect(screen, config["color"], (panel.rect.x + 10, y, 10, 10))
            pygame.draw.rect(screen, WHITE, (panel.rect.x + 10, y, 10, 10), 2)
        else:
            pygame.draw.rect(screen, config["color"], (panel.rect.x + 10, y, 10, 10), 1)
        
        # Mode name
        mode_color = config["color"] if is_current else DARK_GREEN
        mode_text = font_mode.render(f"{key}: {config['name']}", True, mode_color)
        screen.blit(mode_text, (panel.rect.x + 25, y - 2))
        
        # Description
        desc_text = font_mode.render(f"   {config['description']}", True, DARK_GREEN)
        screen.blit(desc_text, (panel.rect.x + 25, y + 10))
        
        y += 35
    
    # Additional info
    y += 10
    pygame.draw.line(screen, DARK_GREEN, (panel.rect.x + 10, y), (panel.rect.x + panel.rect.width - 10, y), 1)
    y += 10
    
    info_lines = [
        "SPACE: Send sonar pulse",
        "←→: Adjust narrow beam"
    ]
    
    for line in info_lines:
        info = font_mode.render(line, True, CYAN)
        screen.blit(info, (panel.rect.x + 10, y))
        y += 15

def draw_system_status(panel):
    """Draw system status panel"""
    font_title = pygame.font.SysFont("Courier New", 13, bold=True)
    font_data = pygame.font.SysFont("Courier New", 11, bold=True)
    
    # Draw the panel background
    panel.draw(screen)
    
    # Draw content
    config = ModeConfig.get_config(current_mode)
    
    y = panel.rect.y + 30
    
    status = [
        ("MODE:", config["name"]),
        ("RANGE:", f"{int(RADAR_RADIUS * config['range_multiplier'] / 17.5)} NM"),
        ("ACCURACY:", f"{int(config['accuracy'] * 100)}%"),
        ("GAIN:", "AUTO (85%)"),
        ("TX STATUS:", "TRANSMITTING")
    ]
    
    for label, value in status:
        label_surf = font_data.render(label, True, GREEN)
        value_surf = font_data.render(value, True, CYAN)
        screen.blit(label_surf, (panel.rect.x + 10, y))
        screen.blit(value_surf, (panel.rect.x + 150, y))
        y += 22

def draw_own_ship_data(panel):
    """Draw own ship data panel"""
    font_title = pygame.font.SysFont("Courier New", 13, bold=True)
    font_data = pygame.font.SysFont("Courier New", 11, bold=True)
    
    # Draw the panel background
    panel.draw(screen)
    
    # Draw content
    y = panel.rect.y + 30
    
    # Simulate slight changes
    own_ship["heading"] = (own_ship["heading"] + random.uniform(-0.1, 0.1)) % 360
    own_ship["speed"] = max(15, min(20, own_ship["speed"] + random.uniform(-0.05, 0.05)))
    
    data = [
        ("HDG:", f"{own_ship['heading']:.1f}°"),
        ("SPD:", f"{own_ship['speed']:.1f} KTS"),
        ("LAT:", own_ship["lat"]),
        ("LON:", own_ship["lon"]),
        ("DEPTH:", f"{own_ship['depth']} M")
    ]
    
    for label, value in data:
        label_surf = font_data.render(label, True, GREEN)
        value_surf = font_data.render(value, True, CYAN)
        screen.blit(label_surf, (panel.rect.x + 10, y))
        screen.blit(value_surf, (panel.rect.x + 150, y))
        y += 22

def draw_tracked_targets(panel):
    """Draw tracked targets panel"""
    font_title = pygame.font.SysFont("Courier New", 13, bold=True)
    font_header = pygame.font.SysFont("Courier New", 10, bold=True)
    font_data = pygame.font.SysFont("Courier New", 9, bold=True)
    
    # Draw the panel background
    panel.draw(screen)
    
    # Draw content
    y = panel.rect.y + 30
    
    # Headers
    headers = ["ID", "RNG", "BRG", "VEL", "THR"]
    header_x = [10, 60, 110, 160, 220]
    
    for i, header in enumerate(headers):
        header_surf = font_header.render(header, True, GREEN)
        screen.blit(header_surf, (panel.rect.x + header_x[i], y))
    
    y += 18
    pygame.draw.line(screen, GREEN, (panel.rect.x + 10, y), (panel.rect.x + panel.rect.width - 10, y), 1)
    y += 8
    
    # Target data
    sorted_targets = sorted(target_manager.targets.values(), key=lambda t: t.distance)
    
    for target in sorted_targets[:15]: 
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
    """Draw acoustic sensor display"""
    font_title = pygame.font.SysFont("Courier New", 13, bold=True)
    font_data = pygame.font.SysFont("Courier New", 11, bold=True)
    
    # Draw the panel background
    panel.draw(screen)
    
    # Draw content
    y = panel.rect.y + 30
    
    # Signal strength bar
    bar_width = int(current_noise_data["intensity"] * 250)
    bar_color = GREEN if current_noise_data["intensity"] < 0.7 else RED
    pygame.draw.rect(screen, bar_color, (panel.rect.x + 10, y, bar_width, 15))
    pygame.draw.rect(screen, GREEN, (panel.rect.x + 10, y, 250, 15), 1)
    
    signal_text = font_data.render(f"{current_noise_data['intensity']:.2f}", True, CYAN)
    screen.blit(signal_text, (panel.rect.x + 265, y))
    
    y += 25
    
    # Frequency and bearing
    info = [
        ("FREQ:", f"{int(current_noise_data['dominant_freq'])} Hz"),
        ("BEARING:", f"{math.degrees(current_noise_data['angle']):.1f}°")
    ]
    
    for label, value in info:
        label_surf = font_data.render(label, True, GREEN)
        value_surf = font_data.render(value, True, CYAN)
        screen.blit(label_surf, (panel.rect.x + 10, y))
        screen.blit(value_surf, (panel.rect.x + 150, y))
        y += 20

def main():
    global sweep_angle, current_mode, narrow_beam_angle, dragged_panel
    
    with stream:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_1:
                        current_mode = DetectionMode.PASSIVE
                    elif event.key == pygame.K_2:
                        current_mode = DetectionMode.ACTIVE_SONAR
                    elif event.key == pygame.K_3:
                        current_mode = DetectionMode.WIDE_BEAM
                    elif event.key == pygame.K_4:
                        current_mode = DetectionMode.NARROW_BEAM
                    elif event.key == pygame.K_5:
                        current_mode = DetectionMode.OMNI_360
                    elif event.key == pygame.K_SPACE:
                        if current_mode == DetectionMode.ACTIVE_SONAR:
                            send_sonar_pulse()
                    elif event.key == pygame.K_LEFT:
                        narrow_beam_angle = (narrow_beam_angle - 5) % 360
                    elif event.key == pygame.K_RIGHT:
                        narrow_beam_angle = (narrow_beam_angle + 5) % 360
                    elif event.key == pygame.K_e:
                        if target_manager.selected_target:
                            print("Export feature - not implemented in this demo")
                    elif event.key == pygame.K_a:
                        print("Export all feature - not implemented in this demo")
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        # Check if clicked on any panel
                        panel_clicked = False
                        for panel in panels:
                            if panel.handle_event(event):
                                panel_clicked = True
                                dragged_panel = panel
                                break
                        
                        # Only select target if not clicking on panel
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

            draw_radar_background()
            draw_sweep_line()
            
            # Update targets based on mode
            config = ModeConfig.get_config(current_mode)
            
            if current_noise_data["intensity"] > 0.3 and current_noise_data["detected_sounds"]:
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
            target_manager.check_collisions()
            
            # Draw all targets
            for target in target_manager.targets.values():
                draw_target(target)
            
            # Draw UI panels (in specific order)
            draw_acoustic_sensor(panels[4])  # ACOUSTIC SENSOR
            draw_mode_selector(panels[0])    # DETECTION MODE
            draw_system_status(panels[1])    # SYSTEM STATUS
            draw_own_ship_data(panels[2])    # OWN SHIP DATA
            draw_tracked_targets(panels[3])  # TRACKED TARGETS
            
            # Draw instructions
            font_inst = pygame.font.SysFont("Courier New", 10, bold=True)
            inst_text = font_inst.render("Drag panel title bars to move. Click to select targets.", True, GRAY)
            screen.blit(inst_text, (10, HEIGHT - 20))
            
            pygame.display.flip()
            
            # Update sweep based on mode
            config = ModeConfig.get_config(current_mode)
            if config["sweep_speed"] > 0:
                sweep_angle = (sweep_angle + config["sweep_speed"]) % 360
            
            clock.tick(FPS)
            
    pygame.quit()

if __name__ == "__main__":
    main()