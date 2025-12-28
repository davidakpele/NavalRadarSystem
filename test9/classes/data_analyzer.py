from test9.utils.config import RADAR_RADIUS
import numpy as np
from collections import deque
import time

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
