import pygame
import math
from test9.classes.sound_system import SoundSystem
from test9.classes.data_analyzer import DataAnalyzer
from test9.classes.three_d_visualizer import ThreeDVisualizer
from test9.classes.mission_scenario import MissionScenario
from test9.classes.session_recorder import SessionRecorder
from test9.classes.target_manager import TargetManager
from test9.components.audio_callback import stream, audio_enabled
from test9.components.analyze_audio import analyze_audio
from test9.utils.config import panels,FPS, clock
from test9.classes.detection_mode import DetectionMode
from test9.classes.mode_config import ModeConfig
from test9.components.process_sonar_echoes import process_sonar_echoes
from test9.components.draw_radar_background import draw_radar_background
from test9.components.draw_sweep_line import draw_sweep_line
from test9.components.draw_target import draw_target
from test9.components.draw_mode_selector import draw_mode_selector
from test9.components.draw_system_status import draw_system_status
from test9.components.draw_own_ship_data import draw_own_ship_data
from test9.components.draw_tracked_targets import draw_tracked_targets
from test9.components.draw_acoustic_sensor import draw_acoustic_sensor
from test9.components.draw_recording_control import draw_recording_control
from test9.components.draw_analytics_dashboard import draw_analytics_dashboard
from test9.components.draw_mission_control import draw_mission_control
from test9.components.get_color import get_color
from test9.components.keyboard_shortcuts_actions import handle_keyboard_shortcuts
from test9.utils.config import RADAR_RADIUS, current_noise_data

# Initialize sound system
sound_system = SoundSystem()

# Initialize 3D visualizer
visualizer_3d = ThreeDVisualizer()

# Initialize data analyzer
data_analyzer = DataAnalyzer()


# Initialize mission system
mission_system = MissionScenario()

# Recording system
recorder = SessionRecorder()

target_manager = TargetManager()


def main():
    """Main application loop"""
    global sweep_angle, current_mode, narrow_beam_angle, dragged_panel
    global zoom_level, paused, brightness, show_grid, show_compass, crt_effect
    global range_setting, gain_control, frequency_filter, noise_gate
    global current_theme_name, theme, WIDTH, HEIGHT, screen
    
    print("╔═══════════════════════════════════════════════════════╗")
    print("║  ADVANCED NAVAL ACOUSTIC RADAR SYSTEM v2.0            ║")
    print("╚═══════════════════════════════════════════════════════╝")
    print("\nPress H for keyboard shortcuts help")
    print("SOUND SYSTEM: Only plays for target detections\n")
    
    # Start audio stream if available
    if stream and audio_enabled:
        stream.start()
    
    # Variables for detection timing
    last_detection_time = {}  # Track last detection time per target
    
    running = True
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if not handle_keyboard_shortcuts(event):
                    running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    # Check panel interaction
                    panel_clicked = False
                    for panel in panels:
                        if panel.handle_event(event):
                            panel_clicked = True
                            dragged_panel = panel
                            sound_system.play_ui_click()
                            break
                    
                    # Select target if not on panel
                    if not panel_clicked:
                        target_manager.select_target_at(event.pos)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    for panel in panels:
                        panel.handle_event(event)
                    dragged_panel = None
            
            elif event.type == pygame.MOUSEMOTION:
                for panel in panels:
                    panel.handle_event(event)
            
            elif event.type == pygame.MOUSEWHEEL:
                # Zoom with mouse wheel
                zoom_level = max(0.5, min(2.0, zoom_level + event.y * 0.1))
            
            elif event.type == pygame.VIDEORESIZE:
                # Handle window resize
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        
        if paused:
            pygame.display.flip()
            clock.tick(FPS)
            continue
        
        # Audio analysis
        analyze_audio()
        
        # Process sonar echoes
        if current_mode == DetectionMode.ACTIVE_SONAR:
            process_sonar_echoes()
        
        # Update mission system
        mission_system.update(target_manager)
        
        # Update analytics
        for target in target_manager.targets.values():
            data_analyzer.add_target_data(target)
        
        
        # Draw radar (2D or 3D)
        if visualizer_3d.enabled:
            visualizer_3d.draw_3d_radar(screen, target_manager.targets, sweep_angle)
        else:
            draw_radar_background()
            draw_sweep_line()
            
            # Draw targets
            for target in target_manager.targets.values():
                draw_target(target)
                    
        # Draw radar
        draw_radar_background()
        draw_sweep_line()
        
        # Target detection and updates
        config = ModeConfig.get_config(current_mode)
        current_time = pygame.time.get_ticks()
        
        # Lower threshold for detection and add debug
        detection_threshold = 0.01  # Very low threshold
        
        if current_noise_data["intensity"] > detection_threshold and current_noise_data["detected_sounds"]:
            detected_angle = math.degrees(current_noise_data["angle"])
            
            # Debug output
            if pygame.time.get_ticks() % 1000 < 20:
                print(f"[DETECT] Angle: {detected_angle:.1f}° | Intensity: {current_noise_data['intensity']:.3f} | Freq: {current_noise_data['dominant_freq']:.0f}Hz")
            
            # Mode-specific detection logic
            should_detect = False
            
            if current_mode == DetectionMode.OMNI_360:
                should_detect = True
            elif current_mode == DetectionMode.NARROW_BEAM:
                angle_diff = abs(detected_angle - narrow_beam_angle)
                if angle_diff > 180:
                    angle_diff = 360 - angle_diff
                if angle_diff < config["detection_arc"] / 2:
                    should_detect = True
            elif current_mode == DetectionMode.WIDE_BEAM:
                angle_diff = abs((sweep_angle % 360) - (detected_angle % 360))
                if angle_diff > 180:
                    angle_diff = 360 - angle_diff
                if angle_diff < config["detection_arc"] / 2:
                    should_detect = True
            else:  # PASSIVE or ACTIVE_SONAR
                angle_diff = abs((sweep_angle % 360) - (detected_angle % 360))
                if angle_diff < 15 or angle_diff > 345:
                    should_detect = True
            
            if should_detect:
                dist = min(current_noise_data["intensity"] * 15 * config["range_multiplier"], RADAR_RADIUS * 0.9)
                types = [s["type"] for s in current_noise_data["detected_sounds"]]
                
                target = target_manager.update_or_create(
                    detected_angle,
                    dist,
                    current_noise_data["intensity"],
                    types,
                    current_noise_data["primary_threat"],
                    current_mode
                )
                
                if target:
                    print(f"[TARGET] Created/Updated target {target.id} at angle {detected_angle:.1f}°, distance {dist:.1f}")
                    
                    # PLAY SOUND ONLY WHEN TARGET IS DETECTED
                    
                    # Only play sound if enough time has passed since last detection for this target
                    # or if it's a new target
                    if (target.id not in last_detection_time or 
                        current_time - last_detection_time[target.id] > 1000):  # 1 second cooldown
                        
                        sound_system.play_target_detection(
                            target.threat_level, 
                            target.intensity
                        )
                        last_detection_time[target.id] = current_time
        
        # Update all targets
        target_manager.update_all()
        target_manager.check_collisions()
        
        # Draw targets
        for target in target_manager.targets.values():
            draw_target(target)
        
        # Draw UI panels
        for i, panel in enumerate(panels):
            if i == 0:
                draw_mode_selector(panel)
            elif i == 1:
                draw_system_status(panel)
            elif i == 2:
                draw_own_ship_data(panel)
            elif i == 3:
                draw_tracked_targets(panel)
            elif i == 4:
                draw_acoustic_sensor(panel)
            elif i == 5:
                draw_recording_control(panel)
            elif i == 6:
                    draw_analytics_dashboard(panel)  
            elif i == 7:
                draw_mission_control(panel)
                
        # Draw status bar
        font_status = pygame.font.SysFont("Courier New", 10, bold=True)
        status_items = [
            f"MODE: {current_mode}",
            f"TARGETS: {len(target_manager.targets)}",
            f"RANGE: {range_setting}NM",
            f"GAIN: {gain_control:.1f}x",
            f"ZOOM: {zoom_level:.1f}x",
            f"FPS: {int(clock.get_fps())}"
        ]
        status_text = " | ".join(status_items)
        status_surf = font_status.render(status_text, True, get_color("primary"))
        screen.blit(status_surf, (10, HEIGHT - 20))
        
        # Recording indicator
        if recorder.recording:
            rec_text = font_status.render("● REC", True, get_color("danger"))
            screen.blit(rec_text, (WIDTH - 80, HEIGHT - 20))
        
        # Add frame to recording
        if recorder.recording and recorder.record_video:
            recorder.add_frame(screen)
        
        # Update display
        pygame.display.flip()
        
        # Update sweep angle (silent - no sweep sounds)
        if config["sweep_speed"] > 0 and not paused:
            sweep_angle = (sweep_angle + config["sweep_speed"]) % 360
        
        clock.tick(FPS)
    
    # Cleanup
    if recorder.recording:
        recorder.stop_recording()
    
    if stream and audio_enabled:
        stream.stop()
        stream.close()
    
    pygame.quit()
    print("\n[SYSTEM] Radar system shutdown complete")

if __name__ == "__main__":
    main()