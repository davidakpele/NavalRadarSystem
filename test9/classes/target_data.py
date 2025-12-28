
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional


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