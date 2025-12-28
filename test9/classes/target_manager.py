import math
from dataclasses import dataclass, asdict
from typing import Dict, Optional
from test9.classes.target import Target
from test9.main import gain_control, recorder, sound_system


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
