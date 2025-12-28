import pygame
from test9.utils.config import RADAR_RADIUS, RADAR_CENTER
from test9.components.get_color import get_color
from test9.main import data_analyzer,  screen



def draw_analytics_dashboard(panel):
    """Draw analytics dashboard panel"""
    if panel.collapsed:
        panel.draw(screen)
        return
        
    font_header = pygame.font.SysFont("Courier New", 10, bold=True)
    font_data = pygame.font.SysFont("Courier New", 9, bold=True)
    
    panel.draw(screen)
    
    y = panel.rect.y + 30
    
    # Get analytics
    trajectories = data_analyzer.analyze_trajectories()
    collisions = data_analyzer.predict_collisions(trajectories)
    stats = data_analyzer.calculate_statistics()
    
    # Statistics
    if stats:
        stats_text = [
            f"Detections: {stats['total_detections']}",
            f"Unique Targets: {stats['unique_targets']}",
            f"Activity: {stats['activity_level']*100:.0f}%",
            f"Avg Velocity: {stats['avg_velocity']:.1f}",
            f"Collision Risks: {len(collisions)}"
        ]
        
        for text in stats_text:
            text_surf = font_data.render(text, True, get_color("primary"))
            screen.blit(text_surf, (panel.rect.x + 10, y))
            y += 18
    
    y += 10
    
    # Threat distribution
    if 'threat_distribution' in stats:
        threat_text = font_header.render("THREAT DISTRIBUTION:", True, get_color("warning"))
        screen.blit(threat_text, (panel.rect.x + 10, y))
        y += 15
        
        threats = [
            ("HOSTILE", get_color("danger"), stats['threat_distribution'].get('HOSTILE', 0)),
            ("UNKNOWN", get_color("warning"), stats['threat_distribution'].get('UNKNOWN', 0)),
            ("NEUTRAL", get_color("primary"), stats['threat_distribution'].get('NEUTRAL', 0)),
            ("FRIENDLY", get_color("accent"), stats['threat_distribution'].get('FRIENDLY', 0))
        ]
        
        for threat_name, color, count in threats:
            bar_width = min(150, count * 20)
            pygame.draw.rect(screen, color, (panel.rect.x + 10, y, bar_width, 10))
            
            text = font_data.render(f"{threat_name}: {count}", True, color)
            screen.blit(text, (panel.rect.x + 20, y + 12))
            y += 25
    
    # Collision warnings
    if collisions:
        y += 10
        warning_text = font_header.render("COLLISION ALERTS:", True, get_color("danger"))
        screen.blit(warning_text, (panel.rect.x + 10, y))
        y += 15
        
        for collision in collisions[:3]:  # Show only first 3
            text = f"T{collision['target1']}-T{collision['target2']}: {collision['probability']*100:.0f}%"
            text_surf = font_data.render(text, True, get_color("danger"))
            screen.blit(text_surf, (panel.rect.x + 10, y))
            y += 15
