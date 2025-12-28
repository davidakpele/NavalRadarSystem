# ============================================================================
# RECORDING & DATA LOGGING
# ============================================================================

import datetime
from typing import Optional
import numpy as np
import pygame
from session_data import SessionData
from target_data import TargetData
from test9.utils.config import WIDTH, HEIGHT, FPS, CHANNELS, FS
from test9.main import current_theme_name, current_mode
import json
import datetime
import csv
import time


class SessionRecorder:
    """Records and manages session data"""
    
    def __init__(self):
        self.recording = False
        self.session_data: Optional[SessionData] = None
        self.frame_buffer = []
        self.max_buffer_size = 3600  # 1 minute at 60 FPS
        self.audio_buffer = []
        self.record_audio = True
        self.record_video = True
        self.selective_recording = False
        
    def start_recording(self):
        """Start a new recording session"""
        session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_data = SessionData(
            session_id=session_id,
            start_time=time.time(),
            metadata={
                "version": "2.0",
                "screen_size": (WIDTH, HEIGHT),
                "fps": FPS,
                "theme": current_theme_name,
                "mode": current_mode
            }
        )
        self.recording = True
        self.frame_buffer = []
        self.audio_buffer = []
        print(f"[RECORDER] Started session: {session_id}")
        
    def stop_recording(self):
        """Stop recording and save session"""
        if not self.recording or not self.session_data:
            return None  # Only return if NOT recording
            
        self.recording = False
        self.session_data.end_time = time.time()
        
        # Save session data
        session_file = f"sessions/session_{self.session_data.session_id}.json"
        self._save_session(session_file)
        
        # Save video if enabled
        if self.record_video and len(self.frame_buffer) > 0:
            video_file = f"recordings/video_{self.session_data.session_id}.mp4"
            self._save_video(video_file)
        
        # Save audio if enabled
        if self.record_audio and len(self.audio_buffer) > 0:
            audio_file = f"recordings/audio_{self.session_data.session_id}.wav"
            self._save_audio(audio_file)
        
        print(f"[RECORDER] Stopped session: {self.session_data.session_id}")
        print(f"[RECORDER] Target events: {len(self.session_data.target_history)}")
        print(f"[RECORDER] Audio samples: {len(self.audio_buffer)}")
        print(f"[RECORDER] Frames buffered: {len(self.frame_buffer)}")
        
        # Print where files were saved
        print(f"[RECORDER] Session saved to: {session_file}")
        
        return self.session_data.session_id
          
    def add_frame(self, surface):
        """Add a frame to the recording buffer"""
        if not self.recording:
            return
            
        # Convert surface to array
        if len(self.frame_buffer) < self.max_buffer_size:
            frame_array = pygame.surfarray.array3d(surface)
            self.frame_buffer.append(frame_array)
    
    def add_audio(self, audio_data):
        """Add audio sample to buffer"""
        if not self.recording or not self.record_audio:
            return
            
        self.audio_buffer.append(audio_data.copy())
    
    def add_target_event(self, target_data: TargetData):
        """Log target detection event"""
        if not self.recording or not self.session_data:
            return
            
        self.session_data.target_history.append(target_data.to_dict())
    
    def add_mode_change(self, mode: str, timestamp: float):
        """Log mode change event"""
        if not self.recording or not self.session_data:
            return
            
        self.session_data.mode_history.append({
            "mode": mode,
            "timestamp": timestamp
        })
    
    def _save_session(self, filename):
        """Save session data to JSON"""
        try:
            # Create a simplified version without large arrays
            save_data = {
                "session_id": self.session_data.session_id,
                "start_time": self.session_data.start_time,
                "end_time": self.session_data.end_time,
                "duration": self.session_data.end_time - self.session_data.start_time,
                "mode_history": self.session_data.mode_history,
                "target_count": len(self.session_data.target_history),
                "targets": self.session_data.target_history[:100],  # Limit to first 100
                "frame_count": len(self.frame_buffer),
                "metadata": self.session_data.metadata
            }
            
            with open(filename, 'w') as f:
                json.dump(save_data, f, indent=2)
                
            # Save detailed target history separately
            if self.session_data.target_history:
                target_file = filename.replace('.json', '_targets.csv')
                self._export_targets_csv(target_file)
            
            print(f"[RECORDER] Session saved to {filename}")
        except Exception as e:
            print(f"[RECORDER] Error saving session: {e}")

    def _save_video(self, filename):
        """Save video frames (placeholder - requires opencv)"""
        print(f"[RECORDER] Video export to {filename} - requires opencv-python")
        print(f"[RECORDER] {len(self.frame_buffer)} frames buffered")
        # Note: Actual video encoding would require: pip install opencv-python
        # Example: cv2.VideoWriter to encode frames
        
    def _save_audio(self, filename):
        """Save audio buffer to WAV file"""
        try:
            import wave
            if len(self.audio_buffer) == 0:
                return
                
            audio_data = np.concatenate(self.audio_buffer)
            
            with wave.open(filename, 'w') as wav_file:
                wav_file.setnchannels(CHANNELS)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(FS)
                wav_file.writeframes((audio_data * 32767).astype(np.int16).tobytes())
                
            print(f"[RECORDER] Audio saved to {filename}")
        except Exception as e:
            print(f"[RECORDER] Error saving audio: {e}")
    
    def _export_targets_csv(self, filename):
        """Export target history to CSV"""
        try:
            if not self.session_data.target_history:
                return
                
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = list(self.session_data.target_history[0].keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for target in self.session_data.target_history:
                    writer.writerow(target)
                    
            print(f"[RECORDER] Target data exported to {filename}")
        except Exception as e:
            print(f"[RECORDER] Error exporting targets: {e}")
