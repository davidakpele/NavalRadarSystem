import pygame
import numpy as np
import sounddevice as sd
import math
from collections import deque
from scipy import signal, fft

WIDTH, HEIGHT = 1400, 900
CENTER = (450, HEIGHT // 2)
RADAR_RADIUS = 350
FPS = 60
FS = 44100 
CHANNELS = 2
CHUNK = 1024 

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Naval Acoustic Radar - Advanced Classification")
clock = pygame.time.Clock()

# Color scheme with threat levels
GREEN = (0, 255, 65)      # Friendly
YELLOW = (255, 255, 0)    # Neutral
RED = (255, 50, 50)       # Threat
DARK_GREEN = (0, 60, 20)
BLACK = (5, 8, 5)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
BLUE = (100, 150, 255)

sweep_angle = 0
blips = deque(maxlen=50) 
current_noise_data = {
    "angle": 0.0, 
    "intensity": 0.0,
    "frequencies": [],
    "dominant_freq": 0.0,
    "detected_sounds": [],  # Can now have multiple
    "primary_threat": "NEUTRAL",
    "confidence": 0.0
}

# Sound classification parameters
VOICE_FREQ_RANGE = (85, 300)
MUSIC_FREQ_RANGE = (20, 4000)
IMPACT_FREQ_RANGE = (50, 8000)
MECHANICAL_FREQ_RANGE = (50, 500)
ALARM_FREQ_RANGE = (2000, 8000)

class Panel:
    """Draggable, resizable, collapsible panel"""
    def __init__(self, x, y, width, height, title, color=GREEN):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_height = 40
        self.title = title
        self.color = color
        self.collapsed = False
        self.dragging = False
        self.resizing = False
        self.drag_offset = (0, 0)
        self.visible = True
        
    def get_title_rect(self):
        return pygame.Rect(self.x, self.y, self.width, 25)
    
    def get_collapse_button_rect(self):
        return pygame.Rect(self.x + self.width - 25, self.y + 5, 15, 15)
    
    def get_close_button_rect(self):
        return pygame.Rect(self.x + self.width - 45, self.y + 5, 15, 15)
    
    def get_resize_handle_rect(self):
        return pygame.Rect(self.x + self.width - 15, 
                          self.y + (self.min_height if self.collapsed else self.height) - 15, 
                          15, 15)
    
    def get_content_rect(self):
        if self.collapsed:
            return None
        return pygame.Rect(self.x, self.y + 25, self.width, self.height - 25)
    
    def handle_event(self, event):
        if not self.visible:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = event.pos
                
                # Check close button
                if self.get_close_button_rect().collidepoint(mouse_pos):
                    self.visible = False
                    return True
                
                # Check collapse button
                if self.get_collapse_button_rect().collidepoint(mouse_pos):
                    self.collapsed = not self.collapsed
                    return True
                
                # Check resize handle
                if self.get_resize_handle_rect().collidepoint(mouse_pos):
                    self.resizing = True
                    return True
                
                # Check title bar for dragging
                if self.get_title_rect().collidepoint(mouse_pos):
                    self.dragging = True
                    self.drag_offset = (mouse_pos[0] - self.x, mouse_pos[1] - self.y)
                    return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
                self.resizing = False
                
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.x = event.pos[0] - self.drag_offset[0]
                self.y = event.pos[1] - self.drag_offset[1]
                # Keep on screen
                self.x = max(0, min(self.x, WIDTH - 100))
                self.y = max(0, min(self.y, HEIGHT - 40))
                return True
            elif self.resizing:
                new_width = max(200, event.pos[0] - self.x)
                new_height = max(self.min_height + 25, event.pos[1] - self.y)
                self.width = min(new_width, WIDTH - self.x)
                if not self.collapsed:
                    self.height = min(new_height, HEIGHT - self.y)
                return True
        
        return False
    
    def draw(self, screen):
        if not self.visible:
            return
        
        height = self.min_height if self.collapsed else self.height
        
        # Draw panel background
        pygame.draw.rect(screen, BLACK, (self.x, self.y, self.width, height))
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, height), 2)
        
        # Draw title bar
        pygame.draw.rect(screen, (20, 20, 20), (self.x, self.y, self.width, 25))
        pygame.draw.line(screen, self.color, 
                        (self.x, self.y + 25), 
                        (self.x + self.width, self.y + 25), 1)
        
        # Draw title
        font = pygame.font.SysFont("Courier New", 12, bold=True)
        title_surf = font.render(self.title, True, CYAN)
        screen.blit(title_surf, (self.x + 8, self.y + 6))
        
        # Draw close button (X)
        close_rect = self.get_close_button_rect()
        pygame.draw.rect(screen, RED, close_rect)
        font_small = pygame.font.SysFont("Arial", 10, bold=True)
        x_surf = font_small.render("X", True, BLACK)
        screen.blit(x_surf, (close_rect.x + 3, close_rect.y + 1))
        
        # Draw collapse button (-)
        collapse_rect = self.get_collapse_button_rect()
        pygame.draw.rect(screen, YELLOW, collapse_rect)
        symbol = "+" if self.collapsed else "-"
        sym_surf = font_small.render(symbol, True, BLACK)
        screen.blit(sym_surf, (collapse_rect.x + 4, collapse_rect.y + 1))
        
        # Draw resize handle
        if not self.collapsed:
            resize_rect = self.get_resize_handle_rect()
            pygame.draw.rect(screen, self.color, resize_rect, 1)
            pygame.draw.line(screen, self.color, 
                           (resize_rect.x + 3, resize_rect.bottom - 3),
                           (resize_rect.right - 3, resize_rect.y + 3), 1)
            pygame.draw.line(screen, self.color, 
                           (resize_rect.x + 6, resize_rect.bottom - 3),
                           (resize_rect.right - 3, resize_rect.y + 6), 1)

# Create panels
classification_panel = Panel(10, 10, 320, 230, "ACOUSTIC CLASSIFIER")
legend_panel = Panel(WIDTH - 210, 10, 200, 130, "THREAT LEGEND")
spectrum_panel = Panel(10, HEIGHT - 150, 400, 140, "FREQUENCY SPECTRUM")
controls_panel = Panel(WIDTH - 210, 150, 200, 200, "CONTROLS")

panels = [classification_panel, legend_panel, spectrum_panel, controls_panel]

class MultiSoundClassifier:
    """Analyzes audio to detect multiple simultaneous sounds"""
    
    @staticmethod
    def analyze_audio(audio_data, sample_rate):
        """Perform frequency analysis on audio data"""
        try:
            # Compute FFT
            fft_data = np.fft.rfft(audio_data)
            fft_freq = np.fft.rfftfreq(len(audio_data), 1/sample_rate)
            magnitude = np.abs(fft_data)
            
            # Find dominant frequency
            dominant_idx = np.argmax(magnitude[1:]) + 1
            dominant_freq = fft_freq[dominant_idx]
            
            # Get top 10 frequencies
            top_indices = np.argsort(magnitude)[-10:]
            top_freqs = fft_freq[top_indices]
            
            return dominant_freq, top_freqs, magnitude, fft_freq
        except:
            return 0.0, [], [], []
    
    @staticmethod
    def detect_multiple_sounds(dominant_freq, magnitude, fft_freq, intensity):
        """Detect multiple sound types simultaneously"""
        
        if len(magnitude) == 0 or len(fft_freq) == 0:
            return [], "NEUTRAL", 0.0
        
        detected_sounds = []
        
        # Calculate spectral characteristics
        spectral_centroid = np.sum(fft_freq * magnitude) / (np.sum(magnitude) + 1e-10)
        spectral_bandwidth = np.sqrt(np.sum(((fft_freq - spectral_centroid) ** 2) * magnitude) / (np.sum(magnitude) + 1e-10))
        
        # Energy in frequency bands
        low_energy = np.sum(magnitude[(fft_freq >= 20) & (fft_freq < 250)])
        mid_energy = np.sum(magnitude[(fft_freq >= 250) & (fft_freq < 2000)])
        high_energy = np.sum(magnitude[(fft_freq >= 2000) & (fft_freq < 8000)])
        total_energy = low_energy + mid_energy + high_energy + 1e-10
        
        low_ratio = low_energy / total_energy
        mid_ratio = mid_energy / total_energy
        high_ratio = high_energy / total_energy
        
        # Peak detection for multiple sound sources
        peaks, _ = signal.find_peaks(magnitude, height=np.max(magnitude) * 0.15, distance=20)
        peak_freqs = fft_freq[peaks]
        
        # Harmonic analysis for music detection
        harmonics_detected = 0
        if len(peak_freqs) > 0:
            base_freq = peak_freqs[0]
            for freq in peak_freqs[1:]:
                ratio = freq / (base_freq + 1e-10)
                if 1.8 < ratio < 2.2 or 2.8 < ratio < 3.2:  # 2nd or 3rd harmonic
                    harmonics_detected += 1
        
        # MUSIC DETECTION (Independent of other sounds)
        if (harmonics_detected >= 2 or 
            (mid_ratio > 0.25 and high_ratio > 0.15 and spectral_bandwidth > 400)):
            confidence = min(0.92, 0.55 + (harmonics_detected * 0.1) + (mid_ratio * 0.3))
            detected_sounds.append({
                "type": "MUSIC",
                "confidence": confidence,
                "threat": "FRIENDLY"
            })
        
        # VOICE DETECTION (Can occur with music)
        voice_energy = np.sum(magnitude[(fft_freq >= 85) & (fft_freq < 300)])
        if (voice_energy / (total_energy + 1e-10) > 0.15 and 
            VOICE_FREQ_RANGE[0] <= dominant_freq <= VOICE_FREQ_RANGE[1]):
            confidence = min(0.88, 0.5 + (voice_energy / total_energy))
            detected_sounds.append({
                "type": "VOICE",
                "confidence": confidence,
                "threat": "FRIENDLY" if intensity < 0.7 else "NEUTRAL"
            })
        
        # IMPACT DETECTION
        if high_ratio > 0.3 and spectral_bandwidth > 1000 and intensity > 0.5:
            confidence = min(0.85, 0.5 + high_ratio * 0.6)
            detected_sounds.append({
                "type": "IMPACT",
                "confidence": confidence,
                "threat": "NEUTRAL" if intensity < 0.9 else "THREAT"
            })
        
        # MECHANICAL DETECTION
        if (low_ratio > 0.5 and spectral_bandwidth < 300 and 
            MECHANICAL_FREQ_RANGE[0] <= dominant_freq <= MECHANICAL_FREQ_RANGE[1]):
            confidence = min(0.88, 0.55 + low_ratio * 0.45)
            detected_sounds.append({
                "type": "MECHANICAL",
                "confidence": confidence,
                "threat": "THREAT" if intensity > 0.8 else "NEUTRAL"
            })
        
        # ALARM DETECTION
        if dominant_freq > 2000 and high_ratio > 0.4:
            confidence = min(0.80, 0.5 + high_ratio * 0.5)
            detected_sounds.append({
                "type": "ALARM",
                "confidence": confidence,
                "threat": "THREAT"
            })
        
        # Determine primary threat level
        if any(s["threat"] == "THREAT" for s in detected_sounds):
            primary_threat = "THREAT"
        elif any(s["threat"] == "NEUTRAL" for s in detected_sounds):
            primary_threat = "NEUTRAL"
        elif any(s["threat"] == "FRIENDLY" for s in detected_sounds):
            primary_threat = "FRIENDLY"
        else:
            primary_threat = "NEUTRAL"
        
        # Average confidence
        avg_confidence = np.mean([s["confidence"] for s in detected_sounds]) if detected_sounds else 0.3
        
        return detected_sounds, primary_threat, avg_confidence

def audio_callback(indata, frames, time, status):
    global current_noise_data
    try:
        left = indata[:, 0]
        right = indata[:, 1]
        mono = (left + right) / 2.0
        intensity = np.linalg.norm(indata)
        
        if intensity > 0.01:
            # Direction finding
            correlation = np.correlate(left, right, mode='full')
            delay = np.argmax(correlation) - (len(left) - 1)
            raw_angle = (delay / 20) * (math.pi / 2)
            
            # Multi-sound classification
            dominant_freq, top_freqs, magnitude, fft_freq = MultiSoundClassifier.analyze_audio(mono, FS)
            detected_sounds, primary_threat, avg_confidence = MultiSoundClassifier.detect_multiple_sounds(
                dominant_freq, magnitude, fft_freq, intensity
            )
            
            current_noise_data["angle"] = float(np.clip(raw_angle, -math.pi/2, math.pi/2))
            current_noise_data["intensity"] = float(intensity)
            current_noise_data["dominant_freq"] = float(dominant_freq)
            current_noise_data["frequencies"] = top_freqs.tolist() if len(top_freqs) > 0 else []
            current_noise_data["detected_sounds"] = detected_sounds
            current_noise_data["primary_threat"] = primary_threat
            current_noise_data["confidence"] = float(avg_confidence)
        else:
            current_noise_data["intensity"] = 0.0
            current_noise_data["detected_sounds"] = []
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
    else:
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

def draw_classification_content(panel):
    """Draw classification panel content"""
    if panel.collapsed or not panel.visible:
        return
    
    x, y = panel.x + 10, panel.y + 35
    font_data = pygame.font.SysFont("Courier New", 11, bold=True)
    
    # Multiple detected sounds
    if current_noise_data["detected_sounds"]:
        label = font_data.render("DETECTED:", True, GREEN)
        screen.blit(label, (x, y))
        y += 20
        
        for i, sound in enumerate(current_noise_data["detected_sounds"]):
            threat_color = get_threat_color(sound["threat"])
            type_text = f"• {sound['type']}"
            conf_text = f"{int(sound['confidence'] * 100)}%"
            
            type_surf = font_data.render(type_text, True, threat_color)
            conf_surf = font_data.render(conf_text, True, CYAN)
            
            screen.blit(type_surf, (x + 5, y))
            screen.blit(conf_surf, (x + 200, y))
            y += 18
    else:
        no_detect = font_data.render("NO DETECTION", True, DARK_GREEN)
        screen.blit(no_detect, (x, y))
        y += 20
    
    y += 5
    pygame.draw.line(screen, DARK_GREEN, (x, y), (x + panel.width - 20, y), 1)
    y += 10
    
    # Overall threat
    threat_label = font_data.render("PRIMARY THREAT:", True, GREEN)
    threat_color = get_threat_color(current_noise_data["primary_threat"])
    threat_value = font_data.render(current_noise_data["primary_threat"], True, threat_color)
    screen.blit(threat_label, (x, y))
    screen.blit(threat_value, (x + 180, y))
    y += 20
    
    # Dominant frequency
    freq_label = font_data.render("DOMINANT FREQ:", True, GREEN)
    freq_value = font_data.render(f"{int(current_noise_data['dominant_freq'])} Hz", True, CYAN)
    screen.blit(freq_label, (x, y))
    screen.blit(freq_value, (x + 180, y))
    y += 20
    
    # Signal strength
    signal_label = font_data.render("SIGNAL:", True, GREEN)
    signal_value = font_data.render(f"{current_noise_data['intensity']:.2f}", True, CYAN)
    screen.blit(signal_label, (x, y))
    screen.blit(signal_value, (x + 180, y))

def draw_legend_content(panel):
    """Draw legend panel content"""
    if panel.collapsed or not panel.visible:
        return
    
    x, y = panel.x + 15, panel.y + 40
    font_item = pygame.font.SysFont("Courier New", 11, bold=True)
    
    items = [
        (GREEN, "FRIENDLY"),
        (YELLOW, "NEUTRAL"),
        (RED, "THREAT")
    ]
    
    for color, label in items:
        pygame.draw.circle(screen, color, (x, y + 5), 6)
        text = font_item.render(label, True, color)
        screen.blit(text, (x + 20, y))
        y += 25

def draw_spectrum_content(panel):
    """Draw spectrum panel content"""
    if panel.collapsed or not panel.visible:
        return
    
    if len(current_noise_data["frequencies"]) > 0:
        bar_width = (panel.width - 40) // 10
        max_freq = max(current_noise_data["frequencies"])
        
        for i, freq in enumerate(current_noise_data["frequencies"][-10:]):
            if max_freq > 0:
                bar_height = int((freq / max_freq) * (panel.height - 60))
                bar_x = panel.x + 20 + i * bar_width
                bar_y = panel.y + panel.height - 20 - bar_height
                
                if freq < 500:
                    bar_color = RED
                elif freq < 2000:
                    bar_color = YELLOW
                else:
                    bar_color = GREEN
                
                pygame.draw.rect(screen, bar_color, (bar_x, bar_y, bar_width - 2, bar_height))

def draw_controls_content(panel):
    """Draw controls panel content"""
    if panel.collapsed or not panel.visible:
        return
    
    x, y = panel.x + 10, panel.y + 40
    font = pygame.font.SysFont("Courier New", 10, bold=True)
    
    controls = [
        "MOUSE CONTROLS:",
        "• Drag title = Move",
        "• Drag corner = Resize",
        "• Click [-] = Collapse",
        "• Click [X] = Close",
        "",
        "KEYBOARD:",
        "• ESC = Exit",
        "• R = Reset panels"
    ]
    
    for text in controls:
        surf = font.render(text, True, GREEN if not text.startswith("•") else CYAN)
        screen.blit(surf, (x, y))
        y += 15

def reset_panels():
    """Reset all panels to default positions"""
    classification_panel.x, classification_panel.y = 10, 10
    classification_panel.width, classification_panel.height = 320, 230
    classification_panel.visible = True
    classification_panel.collapsed = False
    
    legend_panel.x, legend_panel.y = WIDTH - 210, 10
    legend_panel.width, legend_panel.height = 200, 130
    legend_panel.visible = True
    legend_panel.collapsed = False
    
    spectrum_panel.x, spectrum_panel.y = 10, HEIGHT - 150
    spectrum_panel.width, spectrum_panel.height = 400, 140
    spectrum_panel.visible = True
    spectrum_panel.collapsed = False
    
    controls_panel.x, controls_panel.y = WIDTH - 210, 150
    controls_panel.width, controls_panel.height = 200, 200
    controls_panel.visible = True
    controls_panel.collapsed = False

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
                    elif event.key == pygame.K_r:
                        reset_panels()
                
                # Handle panel events
                for panel in reversed(panels):  # Reverse to handle top panel first
                    if panel.handle_event(event):
                        break

            draw_radar_background()
            
            # Draw sweep line
            for i in range(15):
                alpha = 255 - (i * 15)
                trail_angle = math.radians(sweep_angle - i)
                tx = int(CENTER[0] + math.cos(trail_angle) * RADAR_RADIUS)
                ty = int(CENTER[1] + math.sin(trail_angle) * RADAR_RADIUS)
                
                s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                pygame.draw.line(s, (0, 255, 65, alpha), CENTER, (tx, ty), 3)
                screen.blit(s, (0,0))

            # Create blips
            if current_noise_data["intensity"] > 0.3:
                detected_angle = math.degrees(current_noise_data["angle"]) - 90
                angle_diff = abs((sweep_angle % 360) - (detected_angle % 360))
                
                if angle_diff < 15 or angle_diff > 345:
                    dist = min(current_noise_data["intensity"] * 15, RADAR_RADIUS * 0.9)
                    px = int(CENTER[0] + math.cos(math.radians(detected_angle)) * dist)
                    py = int(CENTER[1] + math.sin(math.radians(detected_angle)) * dist)
                    
                    threat_color = get_threat_color(current_noise_data["primary_threat"])
                    
                    types = "+".join([s["type"][:3] for s in current_noise_data["detected_sounds"]])
                    
                    blips.append({
                        "pos": (px, py), 
                        "alpha": 255,
                        "color": threat_color,
                        "types": types,
                        "confidence": current_noise_data["confidence"]
                    })

            # Draw blips
            for blip in list(blips):
                s = pygame.Surface((16, 16), pygame.SRCALPHA)
                pygame.draw.circle(s, (*blip["color"], blip["alpha"]), (8, 8), 7)
                pygame.draw.circle(s, (*blip["color"], blip["alpha"]), (8, 8), 7, 2)
                screen.blit(s, (blip["pos"][0]-8, blip["pos"][1]-8))
                
                if blip["alpha"] > 200 and blip["types"]:
                    font_tiny = pygame.font.SysFont("Courier New", 8, bold=True)
                    type_label = font_tiny.render(blip["types"], True, blip["color"])
                    screen.blit(type_label, (blip["pos"][0] + 10, blip["pos"][1] - 5))
                
                blip["alpha"] -= 3
                if blip["alpha"] <= 0:
                    blips.remove(blip)

            # Draw all panels
            for panel in panels:
                panel.draw(screen)
            
            # Draw panel contents
            draw_classification_content(classification_panel)
            draw_legend_content(legend_panel)
            draw_spectrum_content(spectrum_panel)
            draw_controls_content(controls_panel)

            pygame.display.flip()
            sweep_angle = (sweep_angle + 3) % 360
            clock.tick(FPS)
            
    pygame.quit()

if __name__ == "__main__":
    main()