import pygame
from test9.components.get_color import get_color
from test9.main import mission_system, screen



def draw_mission_control(panel):
    """Draw mission control panel"""
    if panel.collapsed:
        panel.draw(screen)
        return
        
    font_header = pygame.font.SysFont("Courier New", 10, bold=True)
    font_data = pygame.font.SysFont("Courier New", 9, bold=True)
    
    panel.draw(screen)
    
    y = panel.rect.y + 30
    
    # Mission status
    status = "ACTIVE" if mission_system.scenario_running else "STANDBY"
    status_color = get_color("accent") if mission_system.scenario_running else get_color("primary")
    
    status_text = font_header.render(f"MISSION: {status}", True, status_color)
    screen.blit(status_text, (panel.rect.x + 10, y))
    y += 20
    
    if mission_system.scenario_running:
        scenario = mission_system.scenarios.get(mission_system.active_scenario, {})
        name_text = font_data.render(f"Name: {scenario.get('name', 'Unknown')}", True, get_color("primary"))
        screen.blit(name_text, (panel.rect.x + 10, y))
        y += 15
        
        progress = (mission_system.current_step / len(scenario.get('steps', [1]))) * 100
        progress_text = font_data.render(f"Progress: {progress:.0f}%", True, get_color("accent"))
        screen.blit(progress_text, (panel.rect.x + 10, y))
        y += 20
    
    # Scenario buttons (simulated)
    scenarios = ["training", "patrol", "search_rescue", "custom"]
    
    for i, scenario_name in enumerate(scenarios[:3]):  # Show first 3
        scenario = mission_system.scenarios.get(scenario_name, {})
        btn_text = f"[{i+1}] {scenario.get('name', 'Unknown')}"
        text_color = get_color("accent") if mission_system.active_scenario == scenario_name else get_color("primary")
        
        text = font_data.render(btn_text, True, text_color)
        screen.blit(text, (panel.rect.x + 10, y))
        y += 18
    
    # Controls
    y += 10
    controls = [
        "[M] Toggle Mission",
        "[N] Next Scenario",
        "[B] Toggle 3D Mode"
    ]
    
    for control in controls:
        text = font_data.render(control, True, get_color("primary"))
        screen.blit(text, (panel.rect.x + 10, y))
        y += 16
