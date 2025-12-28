
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional

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
