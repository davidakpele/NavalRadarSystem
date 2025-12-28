import pygame
import numpy as np
from dataclasses import dataclass
from test9.main import current_mode
from test9.classes.detection_mode import DetectionMode
from test9.classes.mode_config import ModeConfig

# ============================================================================
# SOUND SYSTEM
# ============================================================================

class SoundSystem:
    """Manages sound effects for the radar system"""
    
    def __init__(self):
        self.sounds = {}
        self.muted = False
        self.master_volume = 0.7
        self.detection_sounds_enabled = True  # Only play sounds for detections
        self.ambient_sounds_enabled = False   # Disable ambient background sounds
        self.sweep_sounds_enabled = False     # Disable sweep sounds
        
        # Initialize sound system with proper channels
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
            pygame.mixer.set_num_channels(16)
            self.sound_initialized = True
        except Exception as e:
            print(f"[SOUND] Failed to initialize sound system: {e}")
            self.sound_initialized = False
            return
        
        # Create synthetic sounds
        self._create_synthetic_sounds()
        
        # Start ambient sounds
        self.start_ambient()
        print("[SOUND] Sound system initialized")
    
    def _create_synthetic_sounds(self):
        """Create synthetic sounds using pygame"""
        if not self.sound_initialized:
            return
            
        try:
            # 1. Radar sweep sound (short beep that sweeps in pitch)
            sweep_length = 200  # ms
            sweep_samples = int(44100 * sweep_length / 1000)
            
            # Create frequency sweep from 800Hz to 1200Hz
            t = np.linspace(0, sweep_length/1000, sweep_samples, False)
            freq = np.linspace(800, 1200, sweep_samples)
            sweep_wave = 0.3 * np.sin(2 * np.pi * freq * t)
            
            # Convert to stereo (2 channels)
            sweep_stereo = np.column_stack((sweep_wave, sweep_wave))
            
            # Convert to pygame sound
            sweep_sound = pygame.sndarray.make_sound(
                (sweep_stereo * 32767).astype(np.int16)
            )
            self.sounds["sweep"] = sweep_sound
            
            # 2. Sonar ping (clean sine wave)
            ping_length = 100  # ms
            ping_samples = int(44100 * ping_length / 1000)
            
            t = np.linspace(0, ping_length/1000, ping_samples, False)
            ping_wave = 0.5 * np.sin(2 * np.pi * 1500 * t)  # 1500Hz ping
            
            # Apply envelope
            envelope = np.ones_like(ping_wave)
            envelope[:10] = np.linspace(0, 1, 10)  # Attack
            envelope[-20:] = np.linspace(1, 0, 20)  # Release
            ping_wave *= envelope
            
            # Convert to stereo
            ping_stereo = np.column_stack((ping_wave, ping_wave))
            
            ping_sound = pygame.sndarray.make_sound(
                (ping_stereo * 32767).astype(np.int16)
            )
            self.sounds["ping"] = ping_sound
            
            # 3. Sonar echo (softer, shorter)
            echo_length = 50  # ms
            echo_samples = int(44100 * echo_length / 1000)
            
            t = np.linspace(0, echo_length/1000, echo_samples, False)
            echo_wave = 0.2 * np.sin(2 * np.pi * 1200 * t)  # 1200Hz echo
            
            # Convert to stereo
            echo_stereo = np.column_stack((echo_wave, echo_wave))
            
            echo_sound = pygame.sndarray.make_sound(
                (echo_stereo * 32767).astype(np.int16)
            )
            self.sounds["echo"] = echo_sound
            
            # 4. Target lock (double beep)
            lock_length = 150  # ms
            lock_samples = int(44100 * lock_length / 1000)
            
            t = np.linspace(0, lock_length/1000, lock_samples, False)
            # Create two pulses
            lock_wave = np.zeros_like(t)
            
            # First pulse at 1000Hz
            pulse1_start = 0
            pulse1_end = int(0.3 * lock_samples)
            t1 = t[pulse1_start:pulse1_end] - t[pulse1_start]
            lock_wave[pulse1_start:pulse1_end] = 0.3 * np.sin(2 * np.pi * 1000 * t1)
            
            # Second pulse at 1200Hz
            pulse2_start = int(0.5 * lock_samples)
            pulse2_end = lock_samples
            t2 = t[pulse2_start:pulse2_end] - t[pulse2_start]
            lock_wave[pulse2_start:pulse2_end] = 0.3 * np.sin(2 * np.pi * 1200 * t2)
            
            # Convert to stereo
            lock_stereo = np.column_stack((lock_wave, lock_wave))
            
            lock_sound = pygame.sndarray.make_sound(
                (lock_stereo * 32767).astype(np.int16)
            )
            self.sounds["target_lock"] = lock_sound
            
            # 5. Warning sound (repeating beep)
            warning_length = 300  # ms
            warning_samples = int(44100 * warning_length / 1000)
            
            t = np.linspace(0, warning_length/1000, warning_samples, False)
            warning_wave = 0.4 * np.sin(2 * np.pi * 800 * t)
            
            # Convert to stereo
            warning_stereo = np.column_stack((warning_wave, warning_wave))
            
            warning_sound = pygame.sndarray.make_sound(
                (warning_stereo * 32767).astype(np.int16)
            )
            self.sounds["warning"] = warning_sound
            
            # 6. Interface click
            click_length = 30  # ms
            click_samples = int(44100 * click_length / 1000)
            
            click_wave = 0.1 * np.random.randn(click_samples)  # White noise click
            envelope = np.ones_like(click_wave)
            envelope[:5] = np.linspace(0, 1, 5)
            envelope[-10:] = np.linspace(1, 0, 10)
            click_wave *= envelope
            
            # Convert to stereo
            click_stereo = np.column_stack((click_wave, click_wave))
            
            click_sound = pygame.sndarray.make_sound(
                (click_stereo * 32767).astype(np.int16)
            )
            self.sounds["click"] = click_sound
            
            # 7. Active sonar pulse (deeper, longer)
            sonar_pulse_length = 500  # ms
            sonar_pulse_samples = int(44100 * sonar_pulse_length / 1000)
            
            t = np.linspace(0, sonar_pulse_length/1000, sonar_pulse_samples, False)
            # Frequency sweep from 300Hz to 1000Hz
            freq = np.linspace(300, 1000, sonar_pulse_samples)
            sonar_pulse_wave = 0.6 * np.sin(2 * np.pi * freq * t)
            
            # Convert to stereo
            sonar_pulse_stereo = np.column_stack((sonar_pulse_wave, sonar_pulse_wave))
            
            sonar_pulse_sound = pygame.sndarray.make_sound(
                (sonar_pulse_stereo * 32767).astype(np.int16)
            )
            self.sounds["sonar_pulse"] = sonar_pulse_sound
            
            # 8. Ambient radar room noise (stereo for more realism)
            ambient_length = 44100 * 2  # 2 seconds of ambient noise
            
            # Create slightly different noise for each channel
            ambient_left = 0.04 * np.random.randn(ambient_length)
            ambient_right = 0.04 * np.random.randn(ambient_length)
            
            # Add low frequency hum
            t = np.linspace(0, 2, ambient_length, False)
            hum_left = 0.02 * np.sin(2 * np.pi * 60 * t)  # 60Hz hum
            hum_right = 0.02 * np.sin(2 * np.pi * 60 * t + 0.1)  # Slightly out of phase
            
            ambient_left += hum_left
            ambient_right += hum_right
            
            # Add occasional static bursts
            for _ in range(10):
                burst_start = np.random.randint(0, ambient_length - 1000)
                burst_length = np.random.randint(100, 500)
                burst_left = 0.08 * np.random.randn(burst_length)
                burst_right = 0.08 * np.random.randn(burst_length)
                ambient_left[burst_start:burst_start+burst_length] += burst_left
                ambient_right[burst_start:burst_start+burst_length] += burst_right
            
            # Combine into stereo array
            ambient_stereo = np.column_stack((ambient_left, ambient_right))
            
            ambient_sound = pygame.sndarray.make_sound(
                (ambient_stereo * 32767).astype(np.int16)
            )
            self.sounds["ambient"] = ambient_sound
            
        except Exception as e:
            print(f"[SOUND] Error creating sounds: {e}")
            import traceback
            traceback.print_exc()
    
    def play_sound(self, sound_name, volume=1.0, loops=0):
        """Play a sound effect"""
        if self.muted or not self.sound_initialized or sound_name not in self.sounds:
            return
        
        try:
            sound = self.sounds[sound_name]
            channel = pygame.mixer.find_channel(True)
            
            if channel:
                channel.set_volume(self.master_volume * volume)
                channel.play(sound, loops)
                return channel
        except Exception as e:
            print(f"[SOUND] Error playing sound {sound_name}: {e}")
    
    def start_ambient(self):
        """Start ambient background sound"""
        if not self.muted and self.sound_initialized and "ambient" in self.sounds:
            try:
                self.ambient_channel = self.play_sound("ambient", volume=0.2, loops=-1)
            except Exception as e:
                print(f"[SOUND] Error starting ambient: {e}")
    
    def stop_ambient(self):
        """Stop ambient sound"""
        if hasattr(self, 'ambient_channel') and self.ambient_channel:
            try:
                self.ambient_channel.stop()
            except:
                pass
    
    def play_radar_sweep(self):
        """Play radar sweep sound based on mode - MODIFIED: Only if enabled"""
        if not self.sound_initialized or not self.sweep_sounds_enabled:
            return
            
        config = ModeConfig.get_config(current_mode)
        
        if current_mode == DetectionMode.PASSIVE:
            # Soft sweep for passive
            self.play_sound("sweep", volume=0.3)
        elif current_mode == DetectionMode.ACTIVE_SONAR:
            # No sweep for active sonar (uses pings)
            pass
        elif current_mode == DetectionMode.WIDE_BEAM:
            # Faster sweep
            self.play_sound("sweep", volume=0.4)
        elif current_mode == DetectionMode.NARROW_BEAM:
            # Slower, more focused sweep
            self.play_sound("sweep", volume=0.5)
        elif current_mode == DetectionMode.OMNI_360:
            # Pulsing sound for omni
            self.play_sound("ping", volume=0.2)
    
    def play_target_detection(self, target_threat, intensity=None):
        """Play sound for target detection based on threat level"""
        if not self.sound_initialized or not self.detection_sounds_enabled:
            return
        
        # Default volumes
        volumes = {
            "HOSTILE": 0.7,
            "UNKNOWN": 0.5,
            "FRIENDLY": 0.3,
            "NEUTRAL": 0.2
        }
        
        base_volume = volumes.get(target_threat, 0.3)
        
        # Adjust volume based on intensity if provided
        if intensity is not None:
            base_volume = min(0.8, base_volume * (1.0 + intensity))
        
        if target_threat == "HOSTILE":
            self.play_sound("warning", volume=base_volume)
            # Also play ping for immediate feedback
            self.play_sound("ping", volume=base_volume * 0.8)
        elif target_threat == "UNKNOWN":
            self.play_sound("ping", volume=base_volume)
        elif target_threat == "FRIENDLY":
            self.play_sound("ping", volume=base_volume)
        else:  # NEUTRAL
            self.play_sound("ping", volume=base_volume)
    
    def play_sonar_pulse(self):
        """Play active sonar pulse sound"""
        if self.sound_initialized:
            self.play_sound("sonar_pulse", volume=0.8)
    
    def play_sonar_echo(self, strength):
        """Play sonar echo return"""
        if self.sound_initialized:
            volume = min(0.6, strength * 0.7)
            self.play_sound("echo", volume=volume)
    
    def play_ui_click(self):
        """Play UI interaction sound"""
        if self.sound_initialized:
            self.play_sound("click", volume=0.15)
    
    def play_mode_change(self):
        """Play sound for mode change"""
        if self.sound_initialized:
            self.play_sound("click", volume=0.25)
    
    def play_target_lock(self):
        """Play sound when target is selected"""
        if self.sound_initialized:
            self.play_sound("target_lock", volume=0.5)
    
    def toggle_mute(self):
        """Toggle sound on/off"""
        if not self.sound_initialized:
            print("[SOUND] Sound system not initialized")
            return
            
        self.muted = not self.muted
        if self.muted:
            pygame.mixer.pause()
            print("[SOUND] Muted")
        else:
            pygame.mixer.unpause()
            print("[SOUND] Unmuted")
    
    def set_volume(self, volume):
        """Set master volume (0.0 to 1.0)"""
        if not self.sound_initialized:
            return
            
        self.master_volume = max(0.0, min(1.0, volume))
        pygame.mixer.set_volume(self.master_volume)

# Initialize sound system with error handling
try:
    sound_system = SoundSystem()
except Exception as e:
    print(f"[ERROR] Failed to initialize sound system: {e}")
    print("[INFO] Continuing without sound...")
    # Create a dummy sound system
    class DummySoundSystem:
        def __init__(self): 
            self.muted = True
            self.master_volume = 0
            self.sound_initialized = False
        def play_sound(self, *args, **kwargs): pass
        def start_ambient(self): pass
        def stop_ambient(self): pass
        def play_radar_sweep(self): pass
        def play_target_detection(self, *args): pass
        def play_sonar_pulse(self): pass
        def play_sonar_echo(self, *args): pass
        def play_ui_click(self): pass
        def play_mode_change(self): pass
        def play_target_lock(self): pass
        def toggle_mute(self): pass
        def set_volume(self, *args): pass
    sound_system = DummySoundSystem()
    