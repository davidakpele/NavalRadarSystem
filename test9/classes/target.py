import pygame
import math
from collections import deque
import time
from test9.utils.config import RADAR_RADIUS,RADAR_CENTER
from test9.components.get_color import get_color
from test9.main import zoom_level, range_setting
from test9.classes.target_data import TargetData
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
