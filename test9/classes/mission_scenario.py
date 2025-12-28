

# ============================================================================
# MISSION SCENARIO SCRIPTING
# ============================================================================

import json
from time import time
import random
from test9.utils.config import RADAR_RADIUS

class MissionScenario:
    """Mission scenario scripting system"""
    
    def __init__(self):
        self.active_scenario = None
        self.scenarios = {}
        self.load_scenarios()
        self.current_step = 0
        self.scenario_timer = 0
        self.scenario_running = False
        
    def load_scenarios(self):
        """Load available scenarios"""
        self.scenarios = {
            "training": {
                "name": "Basic Training",
                "description": "Learn radar operation with simulated targets",
                "steps": [
                    {"time": 0, "action": "spawn", "type": "FRIENDLY", "angle": 45, "range": 0.3},
                    {"time": 5, "action": "spawn", "type": "NEUTRAL", "angle": 90, "range": 0.5},
                    {"time": 10, "action": "spawn", "type": "UNKNOWN", "angle": 135, "range": 0.7},
                    {"time": 15, "action": "spawn", "type": "HOSTILE", "angle": 180, "range": 0.9},
                    {"time": 25, "action": "message", "text": "Training complete!"}
                ]
            },
            "patrol": {
                "name": "Coastal Patrol",
                "description": "Patrol coastal waters for suspicious activity",
                "steps": [
                    {"time": 0, "action": "message", "text": "Begin coastal patrol"},
                    {"time": 3, "action": "spawn", "type": "FRIENDLY", "angle": 30, "range": 0.4},
                    {"time": 8, "action": "spawn", "type": "NEUTRAL", "angle": 120, "range": 0.6},
                    {"time": 15, "action": "spawn", "type": "HOSTILE", "angle": 210, "range": 0.8},
                    {"time": 20, "action": "spawn", "type": "HOSTILE", "angle": 300, "range": 0.5},
                    {"time": 30, "action": "message", "text": "Hostile convoy detected!"},
                    {"time": 35, "action": "objective", "text": "Track hostile targets"}
                ]
            },
            "search_rescue": {
                "name": "Search and Rescue",
                "description": "Locate and identify vessels in distress",
                "steps": [
                    {"time": 0, "action": "message", "text": "Begin search and rescue operation"},
                    {"time": 5, "action": "spawn", "type": "NEUTRAL", "angle": 60, "range": 0.3},
                    {"time": 10, "action": "spawn", "type": "FRIENDLY", "angle": 150, "range": 0.7, "distress": True},
                    {"time": 20, "action": "message", "text": "Distress signal detected!"},
                    {"time": 25, "action": "objective", "text": "Locate the vessel in distress"}
                ]
            },
            "custom": {
                "name": "Custom Scenario",
                "description": "Create your own scenario",
                "steps": []
            }
        }
    
    def start_scenario(self, scenario_name):
        """Start a mission scenario"""
        if scenario_name in self.scenarios:
            self.active_scenario = scenario_name
            self.current_step = 0
            self.scenario_timer = time.time()
            self.scenario_running = True
            print(f"[SCENARIO] Started: {self.scenarios[scenario_name]['name']}")
            return True
        return False
    
    def stop_scenario(self):
        """Stop current scenario"""
        self.scenario_running = False
        self.active_scenario = None
        print("[SCENARIO] Stopped")
    
    def update(self, target_manager):
        """Update scenario progression"""
        if not self.scenario_running or self.active_scenario is None:
            return
            
        scenario = self.scenarios[self.active_scenario]
        elapsed_time = time.time() - self.scenario_timer
        
        # Check for next step
        while (self.current_step < len(scenario["steps"]) and 
               elapsed_time >= scenario["steps"][self.current_step]["time"]):
            step = scenario["steps"][self.current_step]
            self.execute_step(step, target_manager)
            self.current_step += 1
        
        # Check if scenario complete
        if self.current_step >= len(scenario["steps"]):
            print(f"[SCENARIO] {scenario['name']} complete!")
            self.stop_scenario()
    
    def execute_step(self, step, target_manager):
        """Execute a scenario step"""
        action = step.get("action")
        
        if action == "spawn":
            # Spawn a target
            angle = step.get("angle", random.uniform(0, 360))
            distance = step.get("range", 0.5) * RADAR_RADIUS
            threat = step.get("type", "NEUTRAL")
            intensity = step.get("intensity", 0.5)
            
            sound_types = []
            if threat == "HOSTILE":
                sound_types = ["Engine High", "Propeller"]
            elif threat == "FRIENDLY":
                sound_types = ["Engine Low", "Navigation"]
            else:
                sound_types = ["Ambient Noise", "Machinery"]
            
            if step.get("distress"):
                sound_types.append("Distress Signal")
            
            target_manager.update_or_create(
                angle, distance, intensity,
                sound_types, threat, "SCENARIO"
            )
            
            print(f"[SCENARIO] Spawned {threat} target at {angle}°")
            
        elif action == "message":
            # Display message
            text = step.get("text", "")
            print(f"[SCENARIO MESSAGE] {text}")
            # Could add to on-screen message queue here
            
        elif action == "objective":
            # Set objective
            text = step.get("text", "")
            print(f"[SCENARIO OBJECTIVE] {text}")
    
    def create_custom_scenario(self, name, description, steps):
        """Create custom scenario"""
        self.scenarios["custom"] = {
            "name": name,
            "description": description,
            "steps": steps
        }
        print(f"[SCENARIO] Custom scenario '{name}' created")
    
    def save_scenario(self, filename):
        """Save scenario to file"""
        if self.active_scenario:
            with open(filename, 'w') as f:
                json.dump(self.scenarios[self.active_scenario], f, indent=2)
            print(f"[SCENARIO] Saved to {filename}")
