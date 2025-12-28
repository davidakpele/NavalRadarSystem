from test9.utils.config import audio_queue, audio_recording_buffer, CHANNELS, CHUNK, FS
import sounddevice as sd
from test9.main import recorder
# ============================================================================
# AUDIO PROCESSING
# ============================================================================
def audio_callback(indata, frames, time_info, status):
    """Audio callback function for real-time processing"""
    if status:
        print(f"Audio callback status: {status}")
    
    audio_queue.append(indata.copy())
    
    # Add to recording buffer if recording
    if recorder.recording and recorder.record_audio:
        audio_recording_buffer.append(indata.copy())

# Initialize audio stream
try:
    stream = sd.InputStream(
        callback=audio_callback,
        channels=CHANNELS,
        samplerate=FS,
        blocksize=CHUNK
    )
    audio_enabled = True
except Exception as e:
    print(f"Audio initialization error: {e}")
    audio_enabled = False
    stream = None