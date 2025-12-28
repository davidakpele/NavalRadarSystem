from test9.main import get_color
from test9.classes.detection_mode import DetectionMode


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


