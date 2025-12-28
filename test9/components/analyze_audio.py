
import math
from random import random
import numpy as np
import pygame
from test9.utils.config import RADAR_RADIUS, FS
from test9.components.audio_callback import audio_queue, audio_enabled
from test9.main import gain_control, noise_gate, frequency_filter
from scipy import signal, fft

def analyze_audio():
    """Analyze audio for target detection"""
    global current_noise_data
    
    if not audio_enabled or len(audio_queue) == 0:
        return
    
    try:
        audio_data = audio_queue[-1]
        
        # Stereo to mono
        if audio_data.shape[1] == 2:
            audio_mono = np.mean(audio_data, axis=1)
        else:
            audio_mono = audio_data[:, 0]
        
        # Calculate raw intensity BEFORE noise gate
        raw_intensity = np.sqrt(np.mean(audio_mono**2))
        
        # Apply gain control first
        audio_mono_amplified = audio_mono * gain_control
        
        # Apply frequency filter
        if frequency_filter == 'lowpass':
            sos = signal.butter(4, 2000, 'lp', fs=FS, output='sos')
            audio_mono_amplified = signal.sosfilt(sos, audio_mono_amplified)
        elif frequency_filter == 'highpass':
            sos = signal.butter(4, 500, 'hp', fs=FS, output='sos')
            audio_mono_amplified = signal.sosfilt(sos, audio_mono_amplified)
        elif frequency_filter == 'bandpass':
            sos = signal.butter(4, [500, 2000], 'bp', fs=FS, output='sos')
            audio_mono_amplified = signal.sosfilt(sos, audio_mono_amplified)
        
        # Calculate final intensity with much better scaling
        intensity = np.sqrt(np.mean(audio_mono_amplified**2))
        # Scale up significantly for better detection
        intensity = min(intensity * 10.0, 1.0)
        
        # Debug output every 30 frames (about twice per second at 60 FPS)
        if pygame.time.get_ticks() % 500 < 20:
            print(f"[AUDIO] Raw: {raw_intensity:.4f} | Intensity: {intensity:.4f} | Gate: {noise_gate:.2f}")
        
        # Apply noise gate AFTER amplification
        if intensity < noise_gate:
            current_noise_data["intensity"] = 0.0
            return
        
        # FFT analysis
        fft_data = np.fft.fft(audio_mono_amplified)
        freqs = np.fft.fftfreq(len(audio_mono_amplified), 1/FS)
        magnitudes = np.abs(fft_data)[:len(fft_data)//2]
        freqs = freqs[:len(freqs)//2]
        
        # Find dominant frequency
        if len(magnitudes) > 0:
            dominant_idx = np.argmax(magnitudes)
            dominant_freq = abs(freqs[dominant_idx])
        else:
            dominant_freq = 0.0
        
        # Stereo angle detection with better randomization
        if audio_data.shape[1] == 2:
            left = audio_data[:, 0]
            right = audio_data[:, 1]
            
            correlation = np.correlate(left, right, mode='same')
            delay = np.argmax(correlation) - len(correlation) // 2
            angle = (delay / len(correlation)) * math.pi
            # Add some variation
            angle += random.uniform(-0.3, 0.3)
        else:
            angle = random.uniform(0, 2 * math.pi)
        
        # Sound classification - adjusted for human voice (typically 85-255 Hz fundamental, harmonics 200-4000Hz)
        detected_sounds = []
        threat_level = "NEUTRAL"
        
        if dominant_freq < 100:
            detected_sounds.append({"type": "Low Frequency Rumble", "freq": dominant_freq})
            threat_level = "UNKNOWN"
        elif 100 <= dominant_freq < 300:
            detected_sounds.append({"type": "Voice/Engine Low", "freq": dominant_freq})
            threat_level = "UNKNOWN"
        elif 300 <= dominant_freq < 1000:
            detected_sounds.append({"type": "Voice/Machinery", "freq": dominant_freq})
            threat_level = "NEUTRAL"
        elif 1000 <= dominant_freq < 3000:
            detected_sounds.append({"type": "High Voice/Propeller", "freq": dominant_freq})
            threat_level = "HOSTILE"
        else:
            detected_sounds.append({"type": "High Frequency", "freq": dominant_freq})
            threat_level = "NEUTRAL"
        
        # Update global state
        current_noise_data.update({
            "angle": angle,
            "intensity": intensity,
            "frequencies": freqs.tolist()[:100],
            "dominant_freq": dominant_freq,
            "detected_sounds": detected_sounds,
            "primary_threat": threat_level,
            "confidence": min(intensity * 100, 100),
            "range_estimate": min(intensity * 15, RADAR_RADIUS * 0.9)
        })
        
    except Exception as e:
        print(f"[AUDIO] Analysis error: {e}")
        import traceback
        traceback.print_exc()
