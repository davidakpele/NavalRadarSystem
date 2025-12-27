import pygame
import numpy as np
import sounddevice as sd
import math
from collections import deque
from scipy import signal, fft
import json
import datetime
import os

WIDTH, HEIGHT = 1400, 900
CENTER = (450, HEIGHT // 2)
RADAR_RADIUS = 350
FPS = 60
FS = 44100 
CHANNELS = 2
CHUNK = 1024 

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Naval Acoustic Radar - Advanced Tracking")
clock = pygame.time.Clock()

# Color scheme
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

sweep_angle = 0
current_noise_data = {
    "angle": 0.0, 
    "intensity": 0.0,
    "frequencies": [],
    "dominant_freq": 0.0,
    "detected_sounds": [],
    "primary_threat": "NEUTRAL",
    "confidence": 0.0
}

class Target:
    """Advanced target with velocity, prediction, and tracking"""
    next_id = 1
    
    def __init__(self, angle, distance, intensity, sound_types, threat_level):
        self.id = Target.next_id
        Target.next_id += 1
        
        self.angle = angle  # degrees
        self.distance = distance  # pixels
        self.intensity = intensity
        self.sound_types = sound_types
        self.threat_level = threat_level
        
        # Position tracking
        self.position_history = deque(maxlen=50)
        self.position_history.append((angle, distance, pygame.time.get_ticks()))
        
        # Velocity calculation
        self.velocity = 0.0  # pixels per second
        self.velocity_angle = 0.0  # direction of movement
        self.angular_velocity = 0.0  # degrees per second
        
        # Prediction
        self.predicted_positions = []
        
        # Display properties
        self.alpha = 255
        self.last_update = pygame.time.get_ticks()
        self.is_ghost = False
        self.ghost_start_time = 0
        
        # Selection
        self.selected = False
        self.lock_time = 0
        
        # Track export data
        self.track_data = []
        self.track_data.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "angle": angle,
            "distance": distance,
            "intensity": intensity,
            "sound_types": sound_types,
            "threat_level": threat_level
        })
    
    def update(self, angle, distance, intensity, sound_types, threat_level):
        """Update target with new detection"""
        current_time = pygame.time.get_ticks()
        
        # Add to history
        self.position_history.append((angle, distance, current_time))
        
        # Calculate velocity if we have enough history
        if len(self.position_history) >= 2:
            self._calculate_velocity()
        
        # Update prediction
        self._update_prediction()
        
        # Update properties
        self.angle = angle
        self.distance = distance
        self.intensity = intensity
        self.sound_types = sound_types
        self.threat_level = threat_level
        self.alpha = 255
        self.last_update = current_time
        self.is_ghost = False
        
        # Add to track data
        self.track_data.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "angle": angle,
            "distance": distance,
            "intensity": intensity,
            "sound_types": sound_types,
            "threat_level": threat_level,
            "velocity": self.velocity,
            "velocity_angle": self.velocity_angle
        })
    
    def _calculate_velocity(self):
        """Calculate velocity and direction from position history"""
        if len(self.position_history) < 2:
            return
        
        # Get last two positions
        (angle1, dist1, time1) = self.position_history[-2]
        (angle2, dist2, time2) = self.position_history[-1]
        
        time_delta = (time2 - time1) / 1000.0  # Convert to seconds
        
        if time_delta > 0:
            # Convert polar to cartesian for easier velocity calculation
            x1 = dist1 * math.cos(math.radians(angle1))
            y1 = dist1 * math.sin(math.radians(angle1))
            x2 = dist2 * math.cos(math.radians(angle2))
            y2 = dist2 * math.sin(math.radians(angle2))
            
            # Calculate velocity components
            vx = (x2 - x1) / time_delta
            vy = (y2 - y1) / time_delta
            
            # Calculate speed and direction
            self.velocity = math.sqrt(vx**2 + vy**2)
            self.velocity_angle = math.degrees(math.atan2(vy, vx))
            
            # Calculate angular velocity
            angle_change = angle2 - angle1
            # Handle angle wraparound
            if angle_change > 180:
                angle_change -= 360
            elif angle_change < -180:
                angle_change += 360
            self.angular_velocity = angle_change / time_delta
    
    def _update_prediction(self):
        """Calculate predicted future positions"""
        self.predicted_positions = []
        
        if self.velocity > 1.0:  # Only predict if moving
            # Predict next 5 seconds in 1-second intervals
            for t in range(1, 6):
                # Current position in cartesian
                x = self.distance * math.cos(math.radians(self.angle))
                y = self.distance * math.sin(math.radians(self.angle))
                
                # Velocity components
                vx = self.velocity * math.cos(math.radians(self.velocity_angle))
                vy = self.velocity * math.sin(math.radians(self.velocity_angle))
                
                # Predicted position
                pred_x = x + vx * t
                pred_y = y + vy * t
                
                # Convert back to polar
                pred_dist = math.sqrt(pred_x**2 + pred_y**2)
                pred_angle = math.degrees(math.atan2(pred_y, pred_x))
                
                self.predicted_positions.append((pred_angle, pred_dist))
    
    def fade(self):
        """Fade target if not updated recently"""
        time_since_update = pygame.time.get_ticks() - self.last_update
        
        # Start ghost mode after 500ms of no updates
        if time_since_update > 500 and not self.is_ghost:
            self.is_ghost = True
            self.ghost_start_time = pygame.time.get_ticks()
        
        # Ghost tracking - keep visible for 5 seconds after loss
        if self.is_ghost:
            ghost_duration = pygame.time.get_ticks() - self.ghost_start_time
            if ghost_duration < 5000:  # 5 seconds ghost time
                # Slower fade for ghosts
                self.alpha = max(50, 255 - int((ghost_duration / 5000.0) * 205))
                return True
            else:
                return False
        
        # Normal fade
        if time_since_update > 100:
            self.alpha = max(0, self.alpha - 2)
        
        return self.alpha > 0
    
    def get_position(self):
        """Get current cartesian position for display"""
        angle_rad = math.radians(self.angle - 90)
        px = int(CENTER[0] + math.cos(angle_rad) * self.distance)
        py = int(CENTER[1] + math.sin(angle_rad) * self.distance)
        return (px, py)
    
    def get_color(self):
        """Get display color based on state"""
        if self.is_ghost:
            return (150, 150, 150)  # Gray for ghosts
        elif self.selected:
            return WHITE  # White for selected
        elif self.threat_level == "FRIENDLY":
            return GREEN
        elif self.threat_level == "THREAT":
            return RED
        else:
            return YELLOW
    
    def export_track(self, filename=None):
        """Export track history to JSON file"""
        if filename is None:
            filename = f"track_{self.id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {
            "target_id": self.id,
            "export_time": datetime.datetime.now().isoformat(),
            "total_detections": len(self.track_data),
            "track_data": self.track_data
        }
        
        filepath = os.path.join("tracks", filename)
        os.makedirs("tracks", exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return filepath

class TargetManager:
    """Manages all targets and collision detection"""
    def __init__(self):
        self.targets = {}
        self.selected_target = None
        self.collision_warnings = []
    
    def update_or_create(self, angle, distance, intensity, sound_types, threat_level):
        """Update existing target or create new one"""
        # Check for existing target within 15 degrees and similar distance
        found_target = None
        for tid, target in self.targets.items():
            angle_diff = abs(target.angle - angle)
            if angle_diff > 180:
                angle_diff = 360 - angle_diff
            
            dist_diff = abs(target.distance - distance)
            
            if angle_diff < 15 and dist_diff < 50:
                found_target = target
                break
        
        if found_target:
            found_target.update(angle, distance, intensity, sound_types, threat_level)
        else:
            new_target = Target(angle, distance, intensity, sound_types, threat_level)
            self.targets[new_target.id] = new_target
    
    def update_all(self):
        """Update all targets, remove dead ones"""
        to_remove = []
        for tid, target in self.targets.items():
            if not target.fade():
                to_remove.append(tid)
        
        for tid in to_remove:
            del self.targets[tid]
    
    def check_collisions(self):
        """Check for potential collision paths"""
        self.collision_warnings = []
        
        target_list = list(self.targets.values())
        for i, target1 in enumerate(target_list):
            for target2 in target_list[i+1:]:
                if self._check_collision_pair(target1, target2):
                    self.collision_warnings.append((target1.id, target2.id))
    
    def _check_collision_pair(self, target1, target2):
        """Check if two targets will collide based on predictions"""
        if not target1.predicted_positions or not target2.predicted_positions:
            return False
        
        # Check if any predicted positions are close
        for (angle1, dist1) in target1.predicted_positions:
            for (angle2, dist2) in target2.predicted_positions:
                # Convert to cartesian
                x1 = dist1 * math.cos(math.radians(angle1))
                y1 = dist1 * math.sin(math.radians(angle1))
                x2 = dist2 * math.cos(math.radians(angle2))
                y2 = dist2 * math.sin(math.radians(angle2))
                
                # Check distance
                distance = math.sqrt((x2-x1)**2 + (y2-y1)**2)
                if distance < 50:  # Collision threshold
                    return True
        
        return False
    
    def select_target_at(self, pos):
        """Select target at given screen position"""
        for target in self.targets.values():
            target_pos = target.get_position()
            distance = math.sqrt((pos[0]-target_pos[0])**2 + (pos[1]-target_pos[1])**2)
            if distance < 15:  # Click radius
                if self.selected_target:
                    self.selected_target.selected = False
                target.selected = True
                target.lock_time = pygame.time.get_ticks()
                self.selected_target = target
                return target
        
        # Deselect if clicked empty space
        if self.selected_target:
            self.selected_target.selected = False
            self.selected_target = None
        return None
    
    def export_all_tracks(self):
        """Export all target tracks to JSON"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"all_tracks_{timestamp}.json"
        filepath = os.path.join("tracks", filename)
        os.makedirs("tracks", exist_ok=True)
        
        all_tracks = {
            "export_time": datetime.datetime.now().isoformat(),
            "total_targets": len(self.targets),
            "targets": {}
        }
        
        for tid, target in self.targets.items():
            all_tracks["targets"][tid] = {
                "target_id": tid,
                "current_angle": target.angle,
                "current_distance": target.distance,
                "velocity": target.velocity,
                "track_data": target.track_data
            }
        
        with open(filepath, 'w') as f:
            json.dump(all_tracks, f, indent=2)
        
        return filepath

# Global target manager
target_manager = TargetManager()

class MultiSoundClassifier:
    """Analyzes audio to detect multiple simultaneous sounds"""
    
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
            detected_sounds.append({
                "type": "MUSIC",
                "confidence": confidence,
                "threat": "FRIENDLY"
            })
        
        voice_energy = np.sum(magnitude[(fft_freq >= 85) & (fft_freq < 300)])
        if voice_energy / (total_energy + 1e-10) > 0.15:
            confidence = min(0.88, 0.5 + (voice_energy / total_energy))
            detected_sounds.append({
                "type": "VOICE",
                "confidence": confidence,
                "threat": "FRIENDLY" if intensity < 0.7 else "NEUTRAL"
            })
        
        if high_ratio > 0.3 and spectral_bandwidth > 1000 and intensity > 0.5:
            confidence = min(0.85, 0.5 + high_ratio * 0.6)
            detected_sounds.append({
                "type": "IMPACT",
                "confidence": confidence,
                "threat": "NEUTRAL" if intensity < 0.9 else "THREAT"
            })
        
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
    
    for i in range(1, 5):
        pygame.draw.circle(screen, DARK_GREEN, CENTER, (RADAR_RADIUS // 4) * i, 1)
    
    for i in range(0, 360, 30):
        rad = math.radians(i)
        dest = (int(CENTER[0] + math.cos(rad) * RADAR_RADIUS), 
                int(CENTER[1] + math.sin(rad) * RADAR_RADIUS))
        pygame.draw.line(screen, DARK_GREEN, CENTER, dest, 1)

def draw_target(target):
    """Draw target with velocity vector and predictions"""
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
            
            # Draw prediction markers
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
        vel_length = min(target.velocity * 0.5, 50)  # Scale velocity for display
        vel_angle_rad = math.radians(target.velocity_angle)
        end_x = int(pos[0] + math.cos(vel_angle_rad) * vel_length)
        end_y = int(pos[1] + math.sin(vel_angle_rad) * vel_length)
        
        # Arrow shaft
        pygame.draw.line(screen, color, pos, (end_x, end_y), 2)
        
        # Arrow head
        arrow_angle = math.radians(target.velocity_angle)
        arrow_size = 8
        left_x = end_x - arrow_size * math.cos(arrow_angle - 0.5)
        left_y = end_y - arrow_size * math.sin(arrow_angle - 0.5)
        right_x = end_x - arrow_size * math.cos(arrow_angle + 0.5)
        right_y = end_y - arrow_size * math.sin(arrow_angle + 0.5)
        pygame.draw.polygon(screen, color, [(end_x, end_y), (left_x, left_y), (right_x, right_y)])
    
    # Draw target blip
    if target.is_ghost:
        # Ghost appearance
        s = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, target.alpha), (10, 10), 8, 2)
        pygame.draw.line(s, (*color, target.alpha), (5, 10), (15, 10), 1)
        pygame.draw.line(s, (*color, target.alpha), (10, 5), (10, 15), 1)
        screen.blit(s, (pos[0]-10, pos[1]-10))
    else:
        # Normal blip
        s = pygame.Surface((18, 18), pygame.SRCALPHA)
        if target.selected:
            pygame.draw.circle(s, (*color, target.alpha), (9, 9), 10, 3)
        pygame.draw.circle(s, (*color, target.alpha), (9, 9), 7)
        pygame.draw.circle(s, (*color, target.alpha), (9, 9), 7, 2)
        screen.blit(s, (pos[0]-9, pos[1]-9))
    
    # Draw ID and info
    font_tiny = pygame.font.SysFont("Courier New", 9, bold=True)
    id_text = f"T{target.id}"
    if target.is_ghost:
        id_text += " [GHOST]"
    id_surf = font_tiny.render(id_text, True, color)
    screen.blit(id_surf, (pos[0] + 12, pos[1] - 8))
    
    # Draw velocity text
    if target.velocity > 1.0:
        vel_text = f"{int(target.velocity)} px/s"
        vel_surf = font_tiny.render(vel_text, True, color)
        screen.blit(vel_surf, (pos[0] + 12, pos[1] + 3))

def draw_collision_warnings():
    """Draw collision warning indicators"""
    if not target_manager.collision_warnings:
        return
    
    font = pygame.font.SysFont("Courier New", 12, bold=True)
    y_offset = 10
    
    for (tid1, tid2) in target_manager.collision_warnings:
        warning_text = f"COLLISION WARNING: T{tid1} <-> T{tid2}"
        warning_surf = font.render(warning_text, True, RED)
        
        # Flashing effect
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            screen.blit(warning_surf, (WIDTH - 400, y_offset))
        
        y_offset += 20

def draw_selected_target_info():
    """Draw detailed info for selected target"""
    if not target_manager.selected_target:
        return
    
    target = target_manager.selected_target
    
    # Info panel
    panel_x, panel_y = WIDTH - 320, HEIGHT - 250
    panel_width, panel_height = 310, 240
    
    pygame.draw.rect(screen, BLACK, (panel_x, panel_y, panel_width, panel_height))
    pygame.draw.rect(screen, WHITE, (panel_x, panel_y, panel_width, panel_height), 2)
    
    font_title = pygame.font.SysFont("Courier New", 13, bold=True)
    font_data = pygame.font.SysFont("Courier New", 11, bold=True)
    
    # Title
    title = font_title.render(f"TARGET T{target.id} [LOCKED]", True, WHITE)
    screen.blit(title, (panel_x + 10, panel_y + 8))
    
    y = panel_y + 30
    
    # Info fields
    info = [
        ("STATUS:", "GHOST" if target.is_ghost else "ACTIVE"),
        ("BEARING:", f"{int(target.angle)}°"),
        ("RANGE:", f"{int(target.distance)} px"),
        ("VELOCITY:", f"{int(target.velocity)} px/s"),
        ("VEL ANGLE:", f"{int(target.velocity_angle)}°"),
        ("ANG VEL:", f"{target.angular_velocity:.1f}°/s"),
        ("THREAT:", target.threat_level),
        ("INTENSITY:", f"{target.intensity:.2f}"),
        ("TYPES:", "+".join(target.sound_types[:3])),
        ("DETECTIONS:", str(len(target.track_data)))
    ]
    
    for label, value in info:
        label_surf = font_data.render(label, True, GREEN)
        value_surf = font_data.render(value, True, CYAN)
        screen.blit(label_surf, (panel_x + 10, y))
        screen.blit(value_surf, (panel_x + 150, y))
        y += 18
    
    # Export button hint
    hint = font_data.render("Press 'E' to export track", True, YELLOW)
    screen.blit(hint, (panel_x + 10, panel_y + panel_height - 20))

def draw_controls_panel():
    """Draw controls information"""
    panel_x, panel_y = 10, 10
    panel_width, panel_height = 280, 180
    
    pygame.draw.rect(screen, BLACK, (panel_x, panel_y, panel_width, panel_height))
    pygame.draw.rect(screen, GREEN, (panel_x, panel_y, panel_width, panel_height), 2)
    
    font_title = pygame.font.SysFont("Courier New", 12, bold=True)
    font_text = pygame.font.SysFont("Courier New", 10, bold=True)
    
    title = font_title.render("TRACKING CONTROLS", True, CYAN)
    screen.blit(title, (panel_x + 10, panel_y + 8))
    
    y = panel_y + 30
    
    controls = [
        "MOUSE:",
        "• Click target = Lock/Select",
        "• Click empty = Deselect",
        "",
        "KEYBOARD:",
        "• E = Export selected track",
        "• A = Export all tracks",
        "• ESC = Exit",
        "",
        "FEATURES:",
        "• Green arrows = Velocity",
        "• Cyan dots = Predictions",
        "• Gray blips = Ghost tracks"
    ]
    
    for text in controls:
        color = GREEN if not text.startswith("•") else CYAN
        surf = font_text.render(text, True, color)
        screen.blit(surf, (panel_x + 10, y))
        y += 13

def draw_stats_panel():
    """Draw system statistics"""
    panel_x, panel_y = 10, 200
    panel_width, panel_height = 280, 100
    
    pygame.draw.rect(screen, BLACK, (panel_x, panel_y, panel_width, panel_height))
    pygame.draw.rect(screen, GREEN, (panel_x, panel_y, panel_width, panel_height), 2)
    
    font_title = pygame.font.SysFont("Courier New", 12, bold=True)
    font_data = pygame.font.SysFont("Courier New", 11, bold=True)
    
    title = font_title.render("SYSTEM STATUS", True, CYAN)
    screen.blit(title, (panel_x + 10, panel_y + 8))
    
    y = panel_y + 30
    
    active_targets = sum(1 for t in target_manager.targets.values() if not t.is_ghost)
    ghost_targets = sum(1 for t in target_manager.targets.values() if t.is_ghost)
    
    stats = [
        ("ACTIVE TARGETS:", str(active_targets)),
        ("GHOST TARGETS:", str(ghost_targets)),
        ("COLLISIONS:", str(len(target_manager.collision_warnings))),
        ("SELECTED:", f"T{target_manager.selected_target.id}" if target_manager.selected_target else "NONE")
    ]
    
    for label, value in stats:
        label_surf = font_data.render(label, True, GREEN)
        value_surf = font_data.render(value, True, CYAN)
        screen.blit(label_surf, (panel_x + 10, y))
        screen.blit(value_surf, (panel_x + 180, y))
        y += 18

def main():
    global sweep_angle
    
    with stream:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_e:
                        # Export selected target
                        if target_manager.selected_target:
                            filepath = target_manager.selected_target.export_track()
                            print(f"Track exported: {filepath}")
                    elif event.key == pygame.K_a:
                        # Export all tracks
                        filepath = target_manager.export_all_tracks()
                        print(f"All tracks exported: {filepath}")
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        target_manager.select_target_at(event.pos)

            draw_radar_background()
            
            # Draw sweep line
            for i in range(15):
                alpha = 255 - (i * 15)
                trail_angle = math.radians(sweep_angle - i)
                tx = int(CENTER[0] + math.cos(trail_angle) * RADAR_RADIUS)
                ty = int(CENTER[1] + math.sin(trail_angle) * RADAR_RADIUS)
                
                s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                pygame.draw.line(s, (0, 255, 65, alpha), CENTER, (tx, ty), 3)
                screen.blit(s, (0,0))

            # Update targets
            if current_noise_data["intensity"] > 0.3 and current_noise_data["detected_sounds"]:
                detected_angle = math.degrees(current_noise_data["angle"])
                dist = min(current_noise_data["intensity"] * 15, RADAR_RADIUS * 0.9)
                
                types = [s["type"] for s in current_noise_data["detected_sounds"]]
                
                target_manager.update_or_create(
                    detected_angle,
                    dist,
                    current_noise_data["intensity"],
                    types,
                    current_noise_data["primary_threat"]
                )
            
            target_manager.update_all()
            target_manager.check_collisions()
            
            # Draw all targets
            for target in target_manager.targets.values():
                draw_target(target)
            
            # Draw UI
            draw_controls_panel()
            draw_stats_panel()
            draw_collision_warnings()
            draw_selected_target_info()

            pygame.display.flip()
            sweep_angle = (sweep_angle + 3) % 360
            clock.tick(FPS)
            
    pygame.quit()

if __name__ == "__main__":
    main()