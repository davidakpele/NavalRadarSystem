
import numpy as np
import json
import datetime
import os
import csv



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
