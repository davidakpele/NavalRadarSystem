import math
import pygame
from test9.utils.config import RADAR_RADIUS, RADAR_CENTER
from test9.components.get_color import get_color
from test9.main import zoom_level, screen, target_manager

def draw_target(target):
    """Draw a single target"""
    pos = target.get_position()
    color = target.get_color()
    
    # Convert pos to regular Python floats
    pos = (float(pos[0]), float(pos[1]))
    
    # Validate position
    if math.isnan(pos[0]) or math.isnan(pos[1]):
        print(f"[ERROR] Target {target.id} has NaN position: {pos}")
        return
    
    # Draw trail with validation
    if len(target.trail_points) > 1:
        trail_color = (*color[:3], 100)
        
        # Filter out invalid points from trail and convert to Python floats
        valid_trail_points = []
        for point in target.trail_points:
            # Check if point is valid and convert to Python floats
            try:
                if (isinstance(point, (tuple, list)) and len(point) == 2):
                    # Convert numpy types to Python floats
                    x = float(point[0])
                    y = float(point[1])
                    
                    if not (math.isnan(x) or math.isnan(y) or 
                           not math.isfinite(x) or not math.isfinite(y)):
                        valid_trail_points.append((x, y))
            except (TypeError, ValueError) as e:
                print(f"[WARNING] Target {target.id}: Invalid trail point conversion: {point} - {e}")
        
        # Only draw if we have at least 2 valid points
        if len(valid_trail_points) >= 2:
            try:
                pygame.draw.lines(screen, trail_color, False, valid_trail_points, 1)
            except Exception as e:
                print(f"[ERROR] Target {target.id}: Error drawing trail: {e}")
    
    # Draw target symbol
    size = 8
    if target_manager.selected_target == target:
        size = 12
        # Draw selection ring
        pygame.draw.circle(screen, get_color("accent"), (int(pos[0]), int(pos[1])), 20, 2)
    
    # Draw target icon based on threat
    if target.threat_level == "HOSTILE":
        # Triangle
        points = [
            (pos[0], pos[1] - size),
            (pos[0] - size, pos[1] + size),
            (pos[0] + size, pos[1] + size)
        ]
        # Convert points to integers for pygame
        int_points = [(int(p[0]), int(p[1])) for p in points]
        pygame.draw.polygon(screen, color, int_points)
    elif target.threat_level == "FRIENDLY":
        # Circle
        pygame.draw.circle(screen, color, (int(pos[0]), int(pos[1])), size)
    else:
        # Square
        rect = pygame.Rect(int(pos[0] - size//2), int(pos[1] - size//2), size, size)
        pygame.draw.rect(screen, color, rect)
    
    # Draw ID label
    font = pygame.font.SysFont("Courier New", 9, bold=True)
    id_text = font.render(f"T{target.id}", True, color)
    screen.blit(id_text, (int(pos[0] + 10), int(pos[1] - 10)))
    
    # Draw velocity vector - SIMPLIFIED with numpy type conversion
    if abs(target.velocity) > 1:
        vec_length = min(abs(target.velocity) * 2, 50)
        
        # Ensure velocity_angle is valid
        velocity_angle = float(target.velocity_angle)
        if math.isnan(velocity_angle) or not math.isfinite(velocity_angle):
            velocity_angle = 0.0
        
        # Calculate vector end point
        cos_val = math.cos(velocity_angle)
        sin_val = math.sin(velocity_angle)
        vec_end_x = pos[0] + vec_length * cos_val
        vec_end_y = pos[1] + vec_length * sin_val
        
        # Convert to Python floats
        vec_end_x = float(vec_end_x)
        vec_end_y = float(vec_end_y)
        
        # Draw if endpoints are valid
        if (not math.isnan(vec_end_x) and not math.isnan(vec_end_y) and
            math.isfinite(vec_end_x) and math.isfinite(vec_end_y)):
            
            # Convert to integers for pygame
            end_pos = (int(vec_end_x), int(vec_end_y))
            start_pos = (int(pos[0]), int(pos[1]))
            
            try:
                pygame.draw.line(screen, color, start_pos, end_pos, 2)
                
                # Optional: Draw arrow head
                arrow_size = 5
                arrow_angle = velocity_angle + math.pi
                arrow_points = [
                    end_pos,
                    (int(end_pos[0] + arrow_size * math.cos(arrow_angle + 0.5)),
                     int(end_pos[1] + arrow_size * math.sin(arrow_angle + 0.5))),
                    (int(end_pos[0] + arrow_size * math.cos(arrow_angle - 0.5)),
                     int(end_pos[1] + arrow_size * math.sin(arrow_angle - 0.5)))
                ]
                pygame.draw.polygon(screen, color, arrow_points)
            except Exception as e:
                # Silently skip if there's an error
                pass
    
    # Draw predicted positions
    for pred_angle, pred_dist in target.predicted_positions:
        if math.isnan(pred_angle) or math.isnan(pred_dist):
            continue
            
        try:
            pred_x = RADAR_CENTER[0] + pred_dist * math.cos(math.radians(pred_angle - 90)) * zoom_level
            pred_y = RADAR_CENTER[1] + pred_dist * math.sin(math.radians(pred_angle - 90)) * zoom_level
            
            pred_x = float(pred_x)
            pred_y = float(pred_y)
            
            if not (math.isnan(pred_x) or math.isnan(pred_y)):
                pred_color = (*color[:3], 100)
                pygame.draw.circle(screen, pred_color, (int(pred_x), int(pred_y)), 3)
        except Exception as e:
            # Silently skip
            pass
