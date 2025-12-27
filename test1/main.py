import pygame
import numpy as np
import sounddevice as sd
import math
from collections import deque

WIDTH, HEIGHT = 900, 900
CENTER = (WIDTH // 2, HEIGHT // 2)
RADAR_RADIUS = 400
FPS = 60
FS = 44100 
CHANNELS = 2
CHUNK = 1024 

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Naval Acoustic Radar")
clock = pygame.time.Clock()

GREEN = (0, 255, 65)
DARK_GREEN = (0, 40, 0)
BLACK = (5, 8, 5)

sweep_angle = 0
blips = deque(maxlen=50) 
current_noise_data = {"angle": 0.0, "intensity": 0.0}

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
    screen.fill(BLACK)
    for i in range(1, 5):
        pygame.draw.circle(screen, DARK_GREEN, CENTER, (RADAR_RADIUS // 4) * i, 1)
    for i in range(0, 360, 30):
        rad = math.radians(i)
        dest = (int(CENTER[0] + math.cos(rad) * RADAR_RADIUS), int(CENTER[1] + math.sin(rad) * RADAR_RADIUS))
        pygame.draw.line(screen, DARK_GREEN, CENTER, dest, 1)

def main():
    global sweep_angle
    with stream:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            draw_radar_background()
            sweep_rad = math.radians(sweep_angle)
            
            for i in range(15):
                alpha = 255 - (i * 15)
                trail_angle = math.radians(sweep_angle - i)
                tx = int(CENTER[0] + math.cos(trail_angle) * RADAR_RADIUS)
                ty = int(CENTER[1] + math.sin(trail_angle) * RADAR_RADIUS)
                
                s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                pygame.draw.line(s, (0, 255, 65, alpha), CENTER, (tx, ty), 3)
                screen.blit(s, (0,0))

            if current_noise_data["intensity"] > 0.3:
                detected_angle = math.degrees(current_noise_data["angle"]) - 90
                angle_diff = abs((sweep_angle % 360) - (detected_angle % 360))
                
                if angle_diff < 15 or angle_diff > 345:
                    dist = min(current_noise_data["intensity"] * 15, RADAR_RADIUS * 0.9)
                    px = int(CENTER[0] + math.cos(math.radians(detected_angle)) * dist)
                    py = int(CENTER[1] + math.sin(math.radians(detected_angle)) * dist)
                    blips.append({"pos": (px, py), "alpha": 255})

            for blip in list(blips):
                s = pygame.Surface((12, 12), pygame.SRCALPHA)
                pygame.draw.circle(s, (0, 255, 65, blip["alpha"]), (6, 6), 6)
                screen.blit(s, (blip["pos"][0]-6, blip["pos"][1]-6))
                blip["alpha"] -= 3
                if blip["alpha"] <= 0:
                    blips.remove(blip)

            pygame.draw.rect(screen, BLACK, (10, 10, 220, 110))
            pygame.draw.rect(screen, GREEN, (10, 10, 220, 110), 1)
            font = pygame.font.SysFont("Courier New", 16, bold=True)
            screen.blit(font.render("ACOUSTIC RADAR", True, GREEN), (20, 20))
            screen.blit(font.render(f"SIGNAL: {current_noise_data['intensity']:.2f}", True, GREEN), (20, 45))
            screen.blit(font.render(f"BEARING: {math.degrees(current_noise_data['angle']):.1f} DEG", True, GREEN), (20, 70))

            pygame.display.flip()
            sweep_angle = (sweep_angle + 3) % 360
            clock.tick(FPS)
    pygame.quit()

if __name__ == "__main__":
    main()