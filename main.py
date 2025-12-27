import pygame
import numpy as np
import sounddevice as sd
import math
from collections import deque
import random

# Screen dimensions and layout
WIDTH, HEIGHT = 1600, 900
RADAR_SIZE = 700
RADAR_CENTER = (450, HEIGHT // 2)
RADAR_RADIUS = 320
FPS = 60
FS = 44100 
CHANNELS = 2
CHUNK = 1024 

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Naval Acoustic Radar System")
clock = pygame.time.Clock()

# Colors
GREEN = (0, 255, 65)
DARK_GREEN = (0, 60, 20)
BLACK = (5, 8, 5)
RED = (255, 50, 50)
YELLOW = (255, 255, 0)

# Radar state
sweep_angle = 0
tracked_targets = {}
target_id_counter = 100
current_noise_data = {"angle": 0.0, "intensity": 0.0}

# Own ship data (simulated)
own_ship = {
    "heading": 342.5,
    "speed": 18.2,
    "lat": "34° 02.1' N",
    "lon": "118° 24.9' W"
}

class Target:
    def __init__(self, target_id, angle, distance, intensity):
        self.id = target_id
        self.angle = angle  # degrees
        self.distance = distance  # relative units
        self.intensity = intensity
        self.bearing = angle
        self.range_nm = distance / 50.0  # Convert to nautical miles
        self.course = random.randint(0, 360)
        self.history = deque(maxlen=20)
        self.history.append((angle, distance))
        self.alpha = 255
        self.last_update = pygame.time.get_ticks()
        
    def update(self, angle, distance, intensity):
        self.angle = angle
        self.distance = distance
        self.intensity = intensity
        self.bearing = angle
        self.range_nm = distance / 50.0
        self.history.append((angle, distance))
        self.alpha = 255
        self.last_update = pygame.time.get_ticks()
        
    def fade(self):
        time_since_update = pygame.time.get_ticks() - self.last_update
        if time_since_update > 100:
            self.alpha = max(0, self.alpha - 2)
        return self.alpha > 0

def audio_callback(indata, frames, time, status):
    global current_noise_data
    try:
        left = indata[:, 0]
        right = indata[:, 1]
        intensity = np.linalg.norm(indata)
        
        if intensity > 0.01:
            correlation = np.correlate(left, right, mode='full')
            delay = np.argmax(correlation) - (len(left) - 1)
            raw_angle = (delay / 20) * (math.pi / 2)
            current_noise_data["angle"] = float(np.clip(raw_angle, -math.pi/2, math.pi/2))
            current_noise_data["intensity"] = float(intensity)
        else:
            current_noise_data["intensity"] = 0.0
    except Exception:
        pass

stream = sd.InputStream(channels=CHANNELS, samplerate=FS, callback=audio_callback, blocksize=CHUNK)

def draw_radar_background():
    # Main radar circle background
    radar_rect = pygame.Rect(RADAR_CENTER[0] - RADAR_RADIUS - 50, 
                             RADAR_CENTER[1] - RADAR_RADIUS - 50,
                             (RADAR_RADIUS + 50) * 2, 
                             (RADAR_RADIUS + 50) * 2)
    pygame.draw.rect(screen, BLACK, radar_rect)
    pygame.draw.rect(screen, GREEN, radar_rect, 2)
    
    # Concentric circles
    for i in range(1, 5):
        pygame.draw.circle(screen, DARK_GREEN, RADAR_CENTER, (RADAR_RADIUS // 4) * i, 1)
    
    # Main circle
    pygame.draw.circle(screen, GREEN, RADAR_CENTER, RADAR_RADIUS, 2)
    
    # Radial lines
    for i in range(0, 360, 30):
        rad = math.radians(i)
        dest = (int(RADAR_CENTER[0] + math.cos(rad) * RADAR_RADIUS), 
                int(RADAR_CENTER[1] + math.sin(rad) * RADAR_RADIUS))
        pygame.draw.line(screen, DARK_GREEN, RADAR_CENTER, dest, 1)
    
    # Range rings labels
    font_small = pygame.font.SysFont("Courier New", 12, bold=True)
    for i in range(1, 5):
        radius = (RADAR_RADIUS // 4) * i
        range_nm = i * 5  # 5 NM per ring
        label = font_small.render(f"{range_nm}NM", True, DARK_GREEN)
        screen.blit(label, (RADAR_CENTER[0] + radius + 5, RADAR_CENTER[1] - 10))

def draw_sweep_line():
    sweep_rad = math.radians(sweep_angle)
    
    # Draw trailing sweep effect
    for i in range(25):
        alpha = max(10, 255 - (i * 10))
        trail_angle = math.radians(sweep_angle - i * 2)
        tx = int(RADAR_CENTER[0] + math.cos(trail_angle) * RADAR_RADIUS)
        ty = int(RADAR_CENTER[1] + math.sin(trail_angle) * RADAR_RADIUS)
        
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.line(s, (0, 255, 65, alpha), RADAR_CENTER, (tx, ty), 2)
        screen.blit(s, (0,0))

def update_targets():
    global target_id_counter
    
    if current_noise_data["intensity"] > 0.3:
        detected_angle = math.degrees(current_noise_data["angle"])
        distance = min(current_noise_data["intensity"] * 40, RADAR_RADIUS * 0.9)
        
        # Check if this is a known target (within 15 degrees)
        found_existing = False
        for target_id, target in tracked_targets.items():
            angle_diff = abs(target.angle - detected_angle)
            if angle_diff > 180:
                angle_diff = 360 - angle_diff
            
            if angle_diff < 15:
                target.update(detected_angle, distance, current_noise_data["intensity"])
                found_existing = True
                break
        
        # Create new target if not found
        if not found_existing and len(tracked_targets) < 10:
            tracked_targets[target_id_counter] = Target(
                target_id_counter, 
                detected_angle, 
                distance, 
                current_noise_data["intensity"]
            )
            target_id_counter += 1
    
    # Remove faded targets
    to_remove = []
    for target_id, target in tracked_targets.items():
        if not target.fade():
            to_remove.append(target_id)
    
    for target_id in to_remove:
        del tracked_targets[target_id]

def draw_targets():
    for target_id, target in tracked_targets.items():
        # Calculate position
        angle_rad = math.radians(target.angle - 90)
        px = int(RADAR_CENTER[0] + math.cos(angle_rad) * target.distance)
        py = int(RADAR_CENTER[1] + math.sin(angle_rad) * target.distance)
        
        # Draw target blip
        s = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(s, (0, 255, 65, target.alpha), (10, 10), 8)
        pygame.draw.circle(s, (0, 255, 65, target.alpha), (10, 10), 8, 2)
        screen.blit(s, (px - 10, py - 10))
        
        # Draw target ID
        font_small = pygame.font.SysFont("Courier New", 10, bold=True)
        id_label = font_small.render(f"T{target.id}", True, (0, 255, 65, target.alpha))
        screen.blit(id_label, (px + 12, py - 15))
        
        # Draw history trail
        if len(target.history) > 1:
            points = []
            for i, (hist_angle, hist_dist) in enumerate(target.history):
                angle_rad = math.radians(hist_angle - 90)
                hx = int(RADAR_CENTER[0] + math.cos(angle_rad) * hist_dist)
                hy = int(RADAR_CENTER[1] + math.sin(angle_rad) * hist_dist)
                points.append((hx, hy))
            
            if len(points) > 1:
                s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                pygame.draw.lines(s, (0, 255, 65, target.alpha // 3), False, points, 1)
                screen.blit(s, (0, 0))

def draw_system_status():
    x, y = 950, 30
    w, h = 600, 140
    
    # Panel background
    pygame.draw.rect(screen, BLACK, (x, y, w, h))
    pygame.draw.rect(screen, GREEN, (x, y, w, h), 2)
    
    # Title
    font_title = pygame.font.SysFont("Courier New", 18, bold=True)
    title = font_title.render("SYSTEM STATUS", True, YELLOW)
    screen.blit(title, (x + 10, y + 10))
    
    # System info
    font = pygame.font.SysFont("Courier New", 14, bold=True)
    
    status_lines = [
        ("MODE:", "HEAD UP / NM", GREEN),
        ("RANGE:", "20 NM", GREEN),
        ("GAIN:", "AUTO (85%)", GREEN),
        ("TX STATUS:", "TRANSMITTING", GREEN)
    ]
    
    y_offset = 45
    for label, value, color in status_lines:
        label_surf = font.render(label, True, GREEN)
        value_surf = font.render(value, True, color)
        screen.blit(label_surf, (x + 20, y + y_offset))
        screen.blit(value_surf, (x + 400, y + y_offset))
        y_offset += 22

def draw_own_ship_data():
    x, y = 950, 190
    w, h = 600, 140
    
    # Panel background
    pygame.draw.rect(screen, BLACK, (x, y, w, h))
    pygame.draw.rect(screen, GREEN, (x, y, w, h), 2)
    
    # Title
    font_title = pygame.font.SysFont("Courier New", 18, bold=True)
    title = font_title.render("OWN SHIP DATA", True, YELLOW)
    screen.blit(title, (x + 10, y + 10))
    
    # Ship data
    font = pygame.font.SysFont("Courier New", 14, bold=True)
    
    ship_lines = [
        ("HDG:", f"{own_ship['heading']}°", GREEN),
        ("SPD:", f"{own_ship['speed']} KTS", GREEN),
        ("LAT:", own_ship['lat'], GREEN),
        ("LON:", own_ship['lon'], GREEN)
    ]
    
    y_offset = 45
    for label, value, color in ship_lines:
        label_surf = font.render(label, True, GREEN)
        value_surf = font.render(value, True, color)
        screen.blit(label_surf, (x + 20, y + y_offset))
        screen.blit(value_surf, (x + 400, y + y_offset))
        y_offset += 22

def draw_tracked_targets():
    x, y = 950, 350
    w, h = 600, 380
    
    # Panel background
    pygame.draw.rect(screen, BLACK, (x, y, w, h))
    pygame.draw.rect(screen, GREEN, (x, y, w, h), 2)
    
    # Title
    font_title = pygame.font.SysFont("Courier New", 18, bold=True)
    title = font_title.render("TRACKED TARGETS", True, YELLOW)
    screen.blit(title, (x + 10, y + 10))
    
    # Column headers
    font = pygame.font.SysFont("Courier New", 13, bold=True)
    headers = ["ID", "RNG", "BRG", "COG"]
    header_x = [20, 150, 300, 450]
    
    for i, header in enumerate(headers):
        header_surf = font.render(header, True, GREEN)
        screen.blit(header_surf, (x + header_x[i], y + 40))
    
    # Draw horizontal line
    pygame.draw.line(screen, GREEN, (x + 10, y + 60), (x + w - 10, y + 60), 1)
    
    # Target data
    y_offset = 70
    sorted_targets = sorted(tracked_targets.values(), key=lambda t: t.range_nm)
    
    for target in sorted_targets[:12]:  # Show max 12 targets
        data = [
            f"T{target.id}",
            f"{target.range_nm:.1f}NM",
            f"{int(target.bearing)}°",
            f"{target.course}°"
        ]
        
        for i, text in enumerate(data):
            text_surf = font.render(text, True, GREEN)
            screen.blit(text_surf, (x + header_x[i], y + y_offset))
        
        y_offset += 24
        if y_offset > h - 40:
            break

def draw_alerts():
    x, y = 950, 750
    w, h = 600, 120
    
    # Panel background
    pygame.draw.rect(screen, BLACK, (x, y, w, h))
    pygame.draw.rect(screen, GREEN, (x, y, w, h), 2)
    
    # Title
    font_title = pygame.font.SysFont("Courier New", 18, bold=True)
    title = font_title.render("ALERTS", True, RED)
    screen.blit(title, (x + 10, y + 10))
    
    # Alert status
    font = pygame.font.SysFont("Courier New", 14, bold=True)
    
    # Check for close contacts
    close_targets = [t for t in tracked_targets.values() if t.range_nm < 5.0]
    
    if close_targets:
        alert_text = f"CPA VIOLATION: {len(close_targets)} CONTACT(S) < 5NM"
        alert_surf = font.render(alert_text, True, RED)
        screen.blit(alert_surf, (x + 20, y + 50))
    else:
        alert_surf = font.render("CPA VIOLATION:", True, GREEN)
        none_surf = font.render("NONE", True, GREEN)
        screen.blit(alert_surf, (x + 20, y + 50))
        screen.blit(none_surf, (x + 400, y + 50))

def draw_audio_indicator():
    """Draw a real-time audio level indicator"""
    x, y = 50, HEIGHT - 100
    w, h = 350, 70
    
    pygame.draw.rect(screen, BLACK, (x, y, w, h))
    pygame.draw.rect(screen, GREEN, (x, y, w, h), 2)
    
    font = pygame.font.SysFont("Courier New", 12, bold=True)
    label = font.render("ACOUSTIC SENSOR", True, GREEN)
    screen.blit(label, (x + 10, y + 10))
    
    # Signal strength bar
    bar_width = int(current_noise_data["intensity"] * 200)
    bar_color = GREEN if current_noise_data["intensity"] < 0.7 else RED
    pygame.draw.rect(screen, bar_color, (x + 10, y + 40, bar_width, 15))
    pygame.draw.rect(screen, GREEN, (x + 10, y + 40, 200, 15), 1)
    
    signal_text = font.render(f"{current_noise_data['intensity']:.2f}", True, GREEN)
    screen.blit(signal_text, (x + 220, y + 40))

def main():
    global sweep_angle
    
    screen.fill(BLACK)
    
    with stream:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Draw everything
            screen.fill(BLACK)
            draw_radar_background()
            draw_sweep_line()
            update_targets()
            draw_targets()
            
            # Draw UI panels
            draw_system_status()
            draw_own_ship_data()
            draw_tracked_targets()
            draw_alerts()
            draw_audio_indicator()
            
            pygame.display.flip()
            sweep_angle = (sweep_angle + 2) % 360
            clock.tick(FPS)
            
    pygame.quit()

if __name__ == "__main__":
    main()