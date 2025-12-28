import datetime
import json
import os
from time import time
import pygame
from test9.main import screen, target_manager, recorder, sound_system, mission_system, data_analyzer, visualizer_3d
from test9.classes.data_exporter import DataExporter
from test9.components.print_help import print_help
from test9.components.send_sonar_pulse import send_sonar_pulse
from test9.classes.detection_mode import DetectionMode
from test9.classes.color_theme import ColorTheme


def handle_keyboard_shortcuts(event):
    """Handle keyboard shortcuts"""
    global current_mode, narrow_beam_angle, paused, current_theme_name, theme
    global brightness, show_grid, show_compass, crt_effect, zoom_level
    global range_setting, gain_control, frequency_filter, noise_gate
    
    if event.key == pygame.K_ESCAPE:
        return False  # Exit
    
    # Mode selection (1-5)
    elif event.key == pygame.K_1:
        current_mode = DetectionMode.PASSIVE
        recorder.add_mode_change(current_mode, time.time())
        sound_system.play_mode_change()  # NEW
    elif event.key == pygame.K_2:
        current_mode = DetectionMode.ACTIVE_SONAR
        recorder.add_mode_change(current_mode, time.time())
        sound_system.play_mode_change()  # NEW
    elif event.key == pygame.K_3:
        current_mode = DetectionMode.WIDE_BEAM
        recorder.add_mode_change(current_mode, time.time())
        sound_system.play_mode_change()  # NEW
    elif event.key == pygame.K_4:
        current_mode = DetectionMode.NARROW_BEAM
        recorder.add_mode_change(current_mode, time.time())
        sound_system.play_mode_change()  # NEW
    elif event.key == pygame.K_5:
        current_mode = DetectionMode.OMNI_360
        recorder.add_mode_change(current_mode, time.time())
        sound_system.play_mode_change() 
    
    elif event.key == pygame.K_l:
        # Toggle all detection sounds
        sound_system.detection_sounds_enabled = not sound_system.detection_sounds_enabled
        status = "ENABLED" if sound_system.detection_sounds_enabled else "DISABLED"
        print(f"[SOUND] Detection sounds {status}")
        sound_system.play_ui_click()
    
    elif event.key == pygame.K_k:
        # Toggle sweep sounds
        sound_system.sweep_sounds_enabled = not sound_system.sweep_sounds_enabled
        status = "ENABLED" if sound_system.sweep_sounds_enabled else "DISABLED"
        print(f"[SOUND] Sweep sounds {status}")
        sound_system.play_ui_click()
        
    # Active sonar pulse
    elif event.key == pygame.K_SPACE:
        if current_mode == DetectionMode.ACTIVE_SONAR:
            send_sonar_pulse()
            sound_system.play_sonar_pulse()  # NEW
        else:
            paused = not paused
            sound_system.play_ui_click()  # NEW
    
    # Narrow beam control
    elif event.key == pygame.K_LEFT:
        narrow_beam_angle = (narrow_beam_angle - 5) % 360
        sound_system.play_ui_click()  # NEW
    elif event.key == pygame.K_RIGHT:
        narrow_beam_angle = (narrow_beam_angle + 5) % 360
        sound_system.play_ui_click()  # NEW
    
    # Recording controls
    elif event.key == pygame.K_r:
        if recorder.recording:
            recorder.stop_recording()
        else:
            recorder.start_recording()
        sound_system.play_ui_click()  # NEW
    
    elif event.key == pygame.K_s:
        # Screenshot
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshots/screenshot_{timestamp}.png"
        
        # Ensure directory exists
        os.makedirs("screenshots", exist_ok=True)
        
        try:
            pygame.image.save(screen, filename)
            print(f"[SCREENSHOT] Saved to {filename}")
            sound_system.play_ui_click()
        except Exception as e:
            print(f"[SCREENSHOT] Error saving: {e}")
    
    # Sound controls (NEW)
    elif event.key == pygame.K_v:
        sound_system.toggle_mute()
    elif event.key == pygame.K_UP:
        sound_system.set_volume(min(1.0, sound_system.master_volume + 0.1))
        print(f"[VOLUME] {sound_system.master_volume:.1f}")
    elif event.key == pygame.K_DOWN:
        sound_system.set_volume(max(0.0, sound_system.master_volume - 0.1))
        print(f"[VOLUME] {sound_system.master_volume:.1f}")
        
    # Export controls
    elif event.key == pygame.K_e:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exports/targets_{timestamp}.csv"
        DataExporter.export_csv(target_manager.targets, filename)
    
    elif event.key == pygame.K_j:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exports/targets_{timestamp}.json"
        DataExporter.export_json(target_manager.targets, filename)
    
    # Clear targets
    elif event.key == pygame.K_c:
        target_manager.clear_all()
        print("[SYSTEM] All targets cleared")
    
    # Theme switching (T + number)
    elif event.key == pygame.K_t:
        themes = list(ColorTheme.THEMES.keys())
        current_index = themes.index(current_theme_name)
        current_theme_name = themes[(current_index + 1) % len(themes)]
        theme = ColorTheme.get_theme(current_theme_name)
        print(f"[THEME] Switched to {current_theme_name}")
    
    # Visual controls
    elif event.key == pygame.K_b:
        brightness = min(1.0, brightness + 0.1)
    elif event.key == pygame.K_d:
        brightness = max(0.3, brightness - 0.1)
    elif event.key == pygame.K_g:
        show_grid = not show_grid
    elif event.key == pygame.K_o:
        show_compass = not show_compass
    elif event.key == pygame.K_x:
        crt_effect = not crt_effect
    
    # Zoom controls
    elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
        zoom_level = min(2.0, zoom_level + 0.1)
    elif event.key == pygame.K_MINUS:
        zoom_level = max(0.5, zoom_level - 0.1)
    elif event.key == pygame.K_0:
        zoom_level = 1.0
    
    # Range controls
    elif event.key == pygame.K_LEFTBRACKET:
        range_setting = max(5, range_setting - 5)
        print(f"[RANGE] {range_setting} NM")
    elif event.key == pygame.K_RIGHTBRACKET:
        range_setting = min(100, range_setting + 5)
        print(f"[RANGE] {range_setting} NM")
    
    # Gain control
    elif event.key == pygame.K_PERIOD:
        gain_control = min(3.0, gain_control + 0.1)
        print(f"[GAIN] {gain_control:.1f}x")
    elif event.key == pygame.K_COMMA:
        gain_control = max(0.1, gain_control - 0.1)
        print(f"[GAIN] {gain_control:.1f}x")
    
    # Frequency filter
    elif event.key == pygame.K_f:
        filters = [None, 'lowpass', 'highpass', 'bandpass']
        current_idx = filters.index(frequency_filter) if frequency_filter in filters else 0
        frequency_filter = filters[(current_idx + 1) % len(filters)]
        print(f"[FILTER] {frequency_filter if frequency_filter else 'NONE'}")
    
    # Noise gate
    elif event.key == pygame.K_n:
        noise_gate = min(0.9, noise_gate + 0.05)
        print(f"[NOISE GATE] {noise_gate:.2f}")
    elif event.key == pygame.K_m:
        noise_gate = max(0.0, noise_gate - 0.05)
        print(f"[NOISE GATE] {noise_gate:.2f}")
    
    # Target size filter
    elif event.key == pygame.K_u:
        target_manager.target_size_filter = min(1.0, target_manager.target_size_filter + 0.05)
        print(f"[SIZE FILTER] {target_manager.target_size_filter:.2f}")
    elif event.key == pygame.K_y:
        target_manager.target_size_filter = max(0.0, target_manager.target_size_filter - 0.05)
        print(f"[SIZE FILTER] {target_manager.target_size_filter:.2f}")
    # Help
    elif event.key == pygame.K_h:
        print_help()
        
    # 3D Mode
    elif event.key == pygame.K_b:
        visualizer_3d.toggle()
        sound_system.play_ui_click()
        
    # Mission Controls
    elif event.key == pygame.K_m:
        if mission_system.scenario_running:
            mission_system.stop_scenario()
        else:
            mission_system.start_scenario("training")
        sound_system.play_ui_click()
    
    elif event.key == pygame.K_n:
        # Cycle through scenarios
        scenarios = list(mission_system.scenarios.keys())
        if mission_system.active_scenario:
            current_index = scenarios.index(mission_system.active_scenario)
            next_scenario = scenarios[(current_index + 1) % len(scenarios)]
        else:
            next_scenario = scenarios[0]
        
        mission_system.start_scenario(next_scenario)
        sound_system.play_ui_click()
    
    # Export analytics
    elif event.key == pygame.K_a:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exports/analytics_{timestamp}.json"
        
        analytics_data = {
            "timestamp": time.time(),
            "statistics": data_analyzer.calculate_statistics(),
            "trajectories": data_analyzer.analyze_trajectories(),
            "collisions": data_analyzer.predict_collisions(data_analyzer.analyze_trajectories()),
            "heatmap": data_analyzer.generate_heatmap().tolist()
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(analytics_data, f, indent=2)
            print(f"[ANALYTICS] Exported to {filename}")
        except Exception as e:
            print(f"[ANALYTICS] Export error: {e}")
    
    return True

