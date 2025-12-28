
# ============================================================================
# 3D VISUALIZATION
# ============================================================================

import math
import pygame
from test9.utils.config import WIDTH, HEIGHT, RADAR_RADIUS
from test9.main import get_color

class ThreeDVisualizer:
    """3D visualization mode for radar data"""
    
    def __init__(self):
        self.enabled = False
        self.camera_distance = 500
        self.camera_angle = 45
        self.camera_height = 200
        self.view_mode = "perspective"  # "perspective" or "topdown"
        self.rotate_speed = 0.5
        
    def toggle(self):
        """Toggle 3D mode"""
        self.enabled = not self.enabled
        print(f"[3D] Mode {'enabled' if self.enabled else 'disabled'}")
        
    def draw_3d_radar(self, screen, targets, sweep_angle):
        """Draw 3D radar visualization"""
        if not self.enabled:
            return
            
        # Create 3D surface
        surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        
        # Draw 3D grid
        self._draw_3d_grid(surf)
        
        # Draw targets in 3D
        for target in targets.values():
            self._draw_3d_target(surf, target)
        
        # Draw 3D sweep line
        self._draw_3d_sweep(surf, sweep_angle)
        
        # Apply to screen
        screen.blit(surf, (0, 0))
        
    def _draw_3d_grid(self, surf):
        """Draw 3D grid"""
        center_x, center_y = WIDTH // 2, HEIGHT // 2
        
        # Draw depth circles
        for i in range(1, 6):
            radius = 50 * i
            for angle in range(0, 360, 30):
                x = center_x + radius * math.cos(math.radians(angle))
                y = center_y - radius * math.sin(math.radians(angle)) * 0.5  # Perspective compression
                depth = i * 0.2
                alpha = int(255 * (1 - depth))
                color = (*get_color("primary")[:3], alpha)
                pygame.draw.circle(surf, color, (int(x), int(y)), 2)
    
    def _draw_3d_target(self, surf, target):
        """Draw target in 3D"""
        center_x, center_y = WIDTH // 2, HEIGHT // 2
        
        # Convert to 3D coordinates
        distance = target.distance
        angle = target.angle
        depth = distance / RADAR_RADIUS
        
        # Perspective projection
        x = center_x + distance * math.cos(math.radians(angle - 90))
        y = center_y - distance * math.sin(math.radians(angle - 90)) * (0.5 + depth * 0.3)
        
        # Size based on intensity and depth
        size = max(4, int(8 * target.intensity * (1 - depth * 0.5)))
        
        # Color based on threat with depth fading
        color = target.get_color()
        faded_color = (*color[:3], int(color[3] * (1 - depth * 0.5)))
        
        # Draw target
        pygame.draw.circle(surf, faded_color, (int(x), int(y)), size)
        
        # Draw depth line
        pygame.draw.line(surf, faded_color, (int(x), int(y)), 
                        (int(x), int(y + size * 2)), 2)
    
    def _draw_3d_sweep(self, surf, sweep_angle):
        """Draw 3D sweep line"""
        center_x, center_y = WIDTH // 2, HEIGHT // 2
        
        # Calculate 3D sweep line
        length = RADAR_RADIUS
        x = center_x + length * math.cos(math.radians(sweep_angle - 90))
        y = center_y - length * math.sin(math.radians(sweep_angle - 90)) * 0.7
        
        # Draw sweep line with gradient
        for i in range(10):
            segment_length = length * (i + 1) / 10
            segment_x = center_x + segment_length * math.cos(math.radians(sweep_angle - 90))
            segment_y = center_y - segment_length * math.sin(math.radians(sweep_angle - 90)) * 0.7
            alpha = int(255 * (1 - i / 10))
            color = (*get_color("accent")[:3], alpha)
            pygame.draw.line(surf, color, (center_x, center_y), 
                            (int(segment_x), int(segment_y)), 2)
