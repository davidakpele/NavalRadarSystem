import pygame
import numpy as np
import sounddevice as sd
import math
from collections import deque
from scipy import signal, fft

WIDTH, HEIGHT = 900, 900
CENTER = (WIDTH // 2, HEIGHT // 2)
RADAR_RADIUS = 400
FPS = 60
FS = 44100 
CHANNELS = 2
CHUNK = 1024 

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Naval Acoustic Radar - Classification System")
clock = pygame.time.Clock()

# Color scheme with threat levels
GREEN = (0, 255, 65)      # Friendly
YELLOW = (255, 255, 0)    # Neutral
RED = (255, 50, 50)       # Threat
DARK_GREEN = (0, 40, 0)
BLACK = (5, 8, 5)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)

sweep_angle = 0
blips = deque(maxlen=50) 
current_noise_data = {
    "angle": 0.0, 
    "intensity": 0.0,
    "frequencies": [],
    "dominant_freq": 0.0,
    "sound_type": "UNKNOWN",
    "threat_level": "NEUTRAL",
    "confidence": 0.0
}

# Sound classification parameters
VOICE_FREQ_RANGE = (85, 255)      # Human voice fundamental frequency range
MUSIC_FREQ_RANGE = (20, 4000)     # Music typically has rich harmonic content
IMPACT_FREQ_RANGE = (50, 8000)    # Impacts have broad spectrum
MECHANICAL_FREQ_RANGE = (50, 500) # Mechanical/motor sounds

class SoundClassifier:
    """Analyzes audio to classify sound types"""
    
    @staticmethod
    def analyze_audio(audio_data, sample_rate):
        """Perform frequency analysis on audio data"""
        try:
            # Compute FFT
            fft_data = np.fft.rfft(audio_data)
            fft_freq = np.fft.rfftfreq(len(audio_data), 1/sample_rate)
            magnitude = np.abs(fft_data)
            
            # Find dominant frequency
            dominant_idx = np.argmax(magnitude[1:]) + 1  # Skip DC component
            dominant_freq = fft_freq[dominant_idx]
            
            # Get top 10 frequencies
            top_indices = np.argsort(magnitude)[-10:]
            top_freqs = fft_freq[top_indices]
            
            return dominant_freq, top_freqs, magnitude, fft_freq
        except:
            return 0.0, [], [], []
    
    @staticmethod
    def classify_sound(dominant_freq, magnitude, fft_freq, intensity):
        """Classify sound type based on frequency characteristics"""
        
        if len(magnitude) == 0 or len(fft_freq) == 0:
            return "UNKNOWN", "NEUTRAL", 0.0
        
        # Calculate spectral characteristics
        spectral_centroid = np.sum(fft_freq * magnitude) / (np.sum(magnitude) + 1e-10)
        spectral_bandwidth = np.sqrt(np.sum(((fft_freq - spectral_centroid) ** 2) * magnitude) / (np.sum(magnitude) + 1e-10))
        
        # Count energy in different frequency bands
        low_energy = np.sum(magnitude[(fft_freq >= 20) & (fft_freq < 250)])
        mid_energy = np.sum(magnitude[(fft_freq >= 250) & (fft_freq < 2000)])
        high_energy = np.sum(magnitude[(fft_freq >= 2000) & (fft_freq < 8000)])
        total_energy = low_energy + mid_energy + high_energy + 1e-10
        
        low_ratio = low_energy / total_energy
        mid_ratio = mid_energy / total_energy
        high_ratio = high_energy / total_energy
        
        confidence = 0.0
        sound_type = "UNKNOWN"
        threat_level = "NEUTRAL"
        
        # Voice detection
        if (VOICE_FREQ_RANGE[0] <= dominant_freq <= VOICE_FREQ_RANGE[1] and 
            mid_ratio > 0.4 and spectral_bandwidth < 800):
            sound_type = "VOICE"
            confidence = min(0.95, 0.6 + mid_ratio * 0.5)
            threat_level = "FRIENDLY" if intensity < 0.7 else "NEUTRAL"
        
        # Music detection - rich harmonic content
        elif (mid_ratio > 0.35 and high_ratio > 0.15 and 
              spectral_bandwidth > 500 and spectral_centroid > 400):
            sound_type = "MUSIC"
            confidence = min(0.90, 0.5 + (mid_ratio + high_ratio) * 0.4)
            threat_level = "FRIENDLY"
        
        # Impact detection - sudden broad spectrum
        elif (high_ratio > 0.3 and spectral_bandwidth > 1000 and intensity > 0.6):
            sound_type = "IMPACT"
            confidence = min(0.85, 0.5 + high_ratio * 0.6)
            threat_level = "NEUTRAL" if intensity < 0.9 else "THREAT"
        
        # Mechanical/motor detection - low frequency steady
        elif (MECHANICAL_FREQ_RANGE[0] <= dominant_freq <= MECHANICAL_FREQ_RANGE[1] and 
              low_ratio > 0.5 and spectral_bandwidth < 300):
            sound_type = "MECHANICAL"
            confidence = min(0.88, 0.55 + low_ratio * 0.45)
            threat_level = "THREAT" if intensity > 0.8 else "NEUTRAL"
        
        # High-pitched/alarm-like sounds
        elif dominant_freq > 2000 and high_ratio > 0.4:
            sound_type = "ALARM"
            confidence = min(0.80, 0.5 + high_ratio * 0.5)
            threat_level = "THREAT"
        
        # Default classification
        else:
            sound_type = "UNKNOWN"
            confidence = 0.3
            threat_level = "NEUTRAL"
        
        return sound_type, threat_level, confidence

def audio_callback(indata, frames, time, status):
    global current_noise_data
    try:
        left = indata[:, 0]
        right = indata[:, 1]
        mono = (left + right) / 2.0  # Convert to mono for classification
        intensity = np.linalg.norm(indata)
        
        if intensity > 0.01:
            # Direction finding
            correlation = np.correlate(left, right, mode='full')
            delay = np.argmax(correlation) - (len(left) - 1)
            raw_angle = (delay / 20) * (math.pi / 2)
            
            # Frequency analysis and classification
            dominant_freq, top_freqs, magnitude, fft_freq = SoundClassifier.analyze_audio(mono, FS)
            sound_type, threat_level, confidence = SoundClassifier.classify_sound(
                dominant_freq, magnitude, fft_freq, intensity
            )
            
            current_noise_data["angle"] = float(np.clip(raw_angle, -math.pi/2, math.pi/2))
            current_noise_data["intensity"] = float(intensity)
            current_noise_data["dominant_freq"] = float(dominant_freq)
            current_noise_data["frequencies"] = top_freqs.tolist() if len(top_freqs) > 0 else []
            current_noise_data["sound_type"] = sound_type
            current_noise_data["threat_level"] = threat_level
            current_noise_data["confidence"] = float(confidence)
        else:
            current_noise_data["intensity"] = 0.0
            current_noise_data["sound_type"] = "UNKNOWN"
            current_noise_data["confidence"] = 0.0
    except Exception as e:
        pass

stream = sd.InputStream(channels=CHANNELS, samplerate=FS, callback=audio_callback, blocksize=CHUNK)

def get_threat_color(threat_level):
    """Return color based on threat level"""
    if threat_level == "FRIENDLY":
        return GREEN
    elif threat_level == "THREAT":
        return RED
    else:  # NEUTRAL
        return YELLOW

def draw_radar_background():
    screen.fill(BLACK)
    
    # Draw range rings
    for i in range(1, 5):
        pygame.draw.circle(screen, DARK_GREEN, CENTER, (RADAR_RADIUS // 4) * i, 1)
    
    # Draw radial lines
    for i in range(0, 360, 30):
        rad = math.radians(i)
        dest = (int(CENTER[0] + math.cos(rad) * RADAR_RADIUS), 
                int(CENTER[1] + math.sin(rad) * RADAR_RADIUS))
        pygame.draw.line(screen, DARK_GREEN, CENTER, dest, 1)

def draw_classification_panel():
    """Draw detailed classification information panel"""
    panel_x, panel_y = 10, 10
    panel_width, panel_height = 280, 200
    
    # Panel background
    pygame.draw.rect(screen, BLACK, (panel_x, panel_y, panel_width, panel_height))
    pygame.draw.rect(screen, GREEN, (panel_x, panel_y, panel_width, panel_height), 2)
    
    font_title = pygame.font.SysFont("Courier New", 14, bold=True)
    font_data = pygame.font.SysFont("Courier New", 12, bold=True)
    
    # Title
    title = font_title.render("ACOUSTIC CLASSIFIER", True, CYAN)
    screen.blit(title, (panel_x + 10, panel_y + 8))
    
    y_offset = 35
    
    # Sound type with color coding
    threat_color = get_threat_color(current_noise_data["threat_level"])
    type_label = font_data.render("TYPE:", True, GREEN)
    type_value = font_data.render(current_noise_data["sound_type"], True, threat_color)
    screen.blit(type_label, (panel_x + 10, panel_y + y_offset))
    screen.blit(type_value, (panel_x + 90, panel_y + y_offset))
    y_offset += 22
    
    # Threat level
    threat_label = font_data.render("THREAT:", True, GREEN)
    threat_value = font_data.render(current_noise_data["threat_level"], True, threat_color)
    screen.blit(threat_label, (panel_x + 10, panel_y + y_offset))
    screen.blit(threat_value, (panel_x + 90, panel_y + y_offset))
    y_offset += 22
    
    # Confidence bar
    conf_label = font_data.render("CONFIDENCE:", True, GREEN)
    screen.blit(conf_label, (panel_x + 10, panel_y + y_offset))
    conf_percent = f"{int(current_noise_data['confidence'] * 100)}%"
    conf_text = font_data.render(conf_percent, True, GREEN)
    screen.blit(conf_text, (panel_x + 200, panel_y + y_offset))
    
    # Confidence bar
    bar_width = int(current_noise_data['confidence'] * 150)
    bar_y = panel_y + y_offset + 18
    pygame.draw.rect(screen, threat_color, (panel_x + 10, bar_y, bar_width, 8))
    pygame.draw.rect(screen, GREEN, (panel_x + 10, bar_y, 150, 8), 1)
    y_offset += 35
    
    # Frequency info
    freq_label = font_data.render("DOMINANT FREQ:", True, GREEN)
    screen.blit(freq_label, (panel_x + 10, panel_y + y_offset))
    freq_value = font_data.render(f"{int(current_noise_data['dominant_freq'])} Hz", True, CYAN)
    screen.blit(freq_value, (panel_x + 150, panel_y + y_offset))
    y_offset += 22
    
    # Signal strength
    signal_label = font_data.render("SIGNAL:", True, GREEN)
    screen.blit(signal_label, (panel_x + 10, panel_y + y_offset))
    signal_value = font_data.render(f"{current_noise_data['intensity']:.2f}", True, CYAN)
    screen.blit(signal_value, (panel_x + 150, panel_y + y_offset))
    y_offset += 22
    
    # Bearing
    bearing_label = font_data.render("BEARING:", True, GREEN)
    screen.blit(bearing_label, (panel_x + 10, panel_y + y_offset))
    bearing_value = font_data.render(f"{math.degrees(current_noise_data['angle']):.1f}°", True, CYAN)
    screen.blit(bearing_value, (panel_x + 150, panel_y + y_offset))

def draw_legend():
    """Draw threat level color legend"""
    legend_x, legend_y = WIDTH - 190, 10
    legend_width, legend_height = 180, 110
    
    pygame.draw.rect(screen, BLACK, (legend_x, legend_y, legend_width, legend_height))
    pygame.draw.rect(screen, GREEN, (legend_x, legend_y, legend_width, legend_height), 2)
    
    font_title = pygame.font.SysFont("Courier New", 12, bold=True)
    font_item = pygame.font.SysFont("Courier New", 11, bold=True)
    
    title = font_title.render("THREAT LEGEND", True, CYAN)
    screen.blit(title, (legend_x + 10, legend_y + 8))
    
    y_offset = 30
    
    # Friendly
    pygame.draw.circle(screen, GREEN, (legend_x + 20, legend_y + y_offset + 5), 6)
    friendly_text = font_item.render("FRIENDLY", True, GREEN)
    screen.blit(friendly_text, (legend_x + 35, legend_y + y_offset))
    y_offset += 25
    
    # Neutral
    pygame.draw.circle(screen, YELLOW, (legend_x + 20, legend_y + y_offset + 5), 6)
    neutral_text = font_item.render("NEUTRAL", True, YELLOW)
    screen.blit(neutral_text, (legend_x + 35, legend_y + y_offset))
    y_offset += 25
    
    # Threat
    pygame.draw.circle(screen, RED, (legend_x + 20, legend_y + y_offset + 5), 6)
    threat_text = font_item.render("THREAT", True, RED)
    screen.blit(threat_text, (legend_x + 35, legend_y + y_offset))

def draw_frequency_spectrum():
    """Draw a mini frequency spectrum display"""
    spec_x, spec_y = 10, HEIGHT - 130
    spec_width, spec_height = 350, 120
    
    pygame.draw.rect(screen, BLACK, (spec_x, spec_y, spec_width, spec_height))
    pygame.draw.rect(screen, GREEN, (spec_x, spec_y, spec_width, spec_height), 2)
    
    font = pygame.font.SysFont("Courier New", 11, bold=True)
    title = font.render("FREQUENCY SPECTRUM", True, CYAN)
    screen.blit(title, (spec_x + 10, spec_y + 8))
    
    # Draw frequency bars if available
    if len(current_noise_data["frequencies"]) > 0:
        bar_width = (spec_width - 40) // 10
        max_freq = max(current_noise_data["frequencies"]) if len(current_noise_data["frequencies"]) > 0 else 1
        
        for i, freq in enumerate(current_noise_data["frequencies"][-10:]):
            if max_freq > 0:
                bar_height = int((freq / max_freq) * (spec_height - 40))
                bar_x = spec_x + 20 + i * bar_width
                bar_y = spec_y + spec_height - 20 - bar_height
                
                # Color based on frequency range
                if freq < 500:
                    bar_color = RED
                elif freq < 2000:
                    bar_color = YELLOW
                else:
                    bar_color = GREEN
                
                pygame.draw.rect(screen, bar_color, (bar_x, bar_y, bar_width - 2, bar_height))

def main():
    global sweep_angle
    with stream:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            draw_radar_background()
            
            # Draw sweep line with trailing effect
            for i in range(15):
                alpha = 255 - (i * 15)
                trail_angle = math.radians(sweep_angle - i)
                tx = int(CENTER[0] + math.cos(trail_angle) * RADAR_RADIUS)
                ty = int(CENTER[1] + math.sin(trail_angle) * RADAR_RADIUS)
                
                s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                pygame.draw.line(s, (0, 255, 65, alpha), CENTER, (tx, ty), 3)
                screen.blit(s, (0,0))

            # Create blips with classification
            if current_noise_data["intensity"] > 0.3:
                detected_angle = math.degrees(current_noise_data["angle"]) - 90
                angle_diff = abs((sweep_angle % 360) - (detected_angle % 360))
                
                if angle_diff < 15 or angle_diff > 345:
                    dist = min(current_noise_data["intensity"] * 15, RADAR_RADIUS * 0.9)
                    px = int(CENTER[0] + math.cos(math.radians(detected_angle)) * dist)
                    py = int(CENTER[1] + math.sin(math.radians(detected_angle)) * dist)
                    
                    threat_color = get_threat_color(current_noise_data["threat_level"])
                    
                    blips.append({
                        "pos": (px, py), 
                        "alpha": 255,
                        "color": threat_color,
                        "type": current_noise_data["sound_type"],
                        "confidence": current_noise_data["confidence"]
                    })

            # Draw blips with color coding
            for blip in list(blips):
                s = pygame.Surface((16, 16), pygame.SRCALPHA)
                pygame.draw.circle(s, (*blip["color"], blip["alpha"]), (8, 8), 7)
                pygame.draw.circle(s, (*blip["color"], blip["alpha"]), (8, 8), 7, 2)
                screen.blit(s, (blip["pos"][0]-8, blip["pos"][1]-8))
                
                # Draw type label
                if blip["alpha"] > 200 and blip["type"] != "UNKNOWN":
                    font_tiny = pygame.font.SysFont("Courier New", 8, bold=True)
                    type_label = font_tiny.render(blip["type"][:3], True, blip["color"])
                    screen.blit(type_label, (blip["pos"][0] + 10, blip["pos"][1] - 5))
                
                blip["alpha"] -= 3
                if blip["alpha"] <= 0:
                    blips.remove(blip)

            # Draw UI panels
            draw_classification_panel()
            draw_legend()
            draw_frequency_spectrum()

            pygame.display.flip()
            sweep_angle = (sweep_angle + 3) % 360
            clock.tick(FPS)
            
    pygame.quit()

if __name__ == "__main__":
    main()