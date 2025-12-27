import numpy as np
from scipy import fft
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import time
import random
from matplotlib.patches import Wedge

class FMCW_Radar_Simulator:
    """
    Enhanced FMCW Radar Simulator with PPI Display
    """
    def __init__(self):
        # Radar Parameters
        self.B = 200e6    # Bandwidth: 200 MHz
        self.T = 200e-6   # Chirp duration: 200 μs
        self.fc = 24e9    # Carrier frequency: 24 GHz (K-band)
        self.fs = 2e6     # Sampling rate: 2 MHz
        self.c = 3e8      # Speed of light
        self.num_samples = int(self.T * self.fs) # 400 samples
        
        # Calculated Limits
        self.lambda_c = self.c / self.fc
        self.R_max = (self.c * self.T * self.fs) / (4 * self.B) # Max unambiguous range (150m)
        self.V_max = self.lambda_c / (4 * self.T) # Max unambiguous velocity (9.375 m/s)
        self.range_res = self.c / (2 * self.B) # Range Resolution (0.75m)
        
        # Time vector
        self.t = np.linspace(0, self.T, self.num_samples, endpoint=False)
        
    def simulate_targets(self, ranges, velocities, rcs):
        """Simulate multiple targets with current range, velocity, and RCS"""
        # Transmit chirp
        tx_chirp = np.exp(1j * 2 * np.pi * (self.fc * self.t + (self.B/(2*self.T)) * self.t**2))
        
        # Initialize received signal
        rx_signal = np.zeros(self.num_samples, dtype=complex)
        
        # Add each target's reflection
        for r_current, vel, rc in zip(ranges, velocities, rcs):
            # Time delay considering velocity
            delay = 2 * (r_current + vel * self.t) / self.c
            
            # Received chirp with attenuation (simple 1/R^2 model)
            attenuation = np.sqrt(rc) / (r_current**2 + 1e-6) 
            
            rx_chirp = attenuation * np.exp(1j * 2 * np.pi * (self.fc * (self.t - delay) + (self.B/(2*self.T)) * (self.t - delay)**2))
            rx_signal += rx_chirp
        
        # Add noise (Complex Gaussian White Noise)
        noise_power = 0.01
        rx_signal += np.sqrt(noise_power/2) * (np.random.randn(self.num_samples) + 
                               1j * np.random.randn(self.num_samples))
        
        return tx_chirp, rx_signal
    
    def range_fft(self, tx_signal, rx_signal):
        """Calculate range FFT (Mix and FFT of beat frequency)."""
        mixed = tx_signal * np.conj(rx_signal)
        window = np.hanning(len(mixed))
        range_fft = fft.fft(mixed * window)
        
        # Calculate range bins
        num_bins = len(range_fft)
        range_bins_per_index = self.c / (2 * self.B) * (self.fs / num_bins) * self.T
        range_bins = np.arange(num_bins) * range_bins_per_index
        
        return range_fft, range_bins

    def cfar_detection(self, range_profile, guard_cells=5, training_cells=15, threshold_factor=1.8):
        """Constant False Alarm Rate target detection (simple 1D CFAR)."""
        # Convert to power and use only positive frequencies (first half)
        power_profile = np.abs(range_profile[:len(range_profile)//2])**2
        num_cells = len(power_profile)
        detected_indices = []
        
        N_train = training_cells
        N_guard = guard_cells
        
        for i in range(N_train + N_guard, num_cells - N_train - N_guard):
            leading = power_profile[i - N_train - N_guard : i - N_guard]
            trailing = power_profile[i + N_guard + 1 : i + N_train + N_guard + 1]
            
            training_cells_combined = np.concatenate([leading, trailing])
            if training_cells_combined.size == 0:
                continue

            noise_floor = np.mean(training_cells_combined)
            threshold = threshold_factor * noise_floor
            
            if power_profile[i] > threshold:
                detected_indices.append(i)
                
        return detected_indices

def main():
    """Enhanced PPI radar simulation with dynamic targets and pulsing sweep (PPI-only display)."""
    
    radar = FMCW_Radar_Simulator()
    frame_time_step = 0.1
    
    # Aesthetic and Persistence Parameters
    BLIP_FADE_RATE = 0.15
    BLIP_MIN_ALPHA = 0.05
    
    # PULSE AESTHETICS
    PULSE_LINE_COLOR = '#ffcc00' # Bright Yellow/Orange
    PULSE_LINE_WIDTH = 8
    DEFAULT_LINE_COLOR = '#ffffff' # Default White
    DEFAULT_LINE_WIDTH = 4
    
    # Initial targets (Range, Velocity, RCS)
    current_ranges = [15.0, 45.0, 80.0, 25.0, 60.0]
    velocities = [5.0, -10.0, 0.0, 8.0, -5.0]
    rcs = [1.0, 0.5, 2.0, 0.8, 1.2]
    
    # Target tracking store (Key is the range bin index)
    target_blips = {}
    
    print("🚀 Enhanced FMCW Radar PPI Simulation")
    print(f"Max Range: {radar.R_max:.1f}m | Max Velocity: {radar.V_max:.1f}m/s")
    
    # Get range bins for processing (not plotting, as the range panel is removed)
    _, range_bins_init = radar.range_fft(
        np.zeros(radar.num_samples), np.zeros(radar.num_samples))
    n_half = len(range_bins_init) // 2
    range_bins_half = range_bins_init[:n_half]
    
    # === PLOT SETUP (PPI Only) ===
    plt.ion()
    # Use a square figure size for the PPI
    fig = plt.figure(figsize=(10, 10), facecolor='black')
    
    # Create the main PPI axis to fill the figure
    ax_ppi = fig.add_subplot(111, projection='polar')
    
    # PPI Configuration
    max_display_range = 100
    theme_color = '#00ff41' # Bright green
    
    # --- Setup PPI AXIS ---
    ax_ppi.set_facecolor('black')
    ax_ppi.spines['polar'].set_color('none')
    ax_ppi.grid(True, color=theme_color, alpha=0.3, linestyle='--')
    ax_ppi.set_theta_zero_location("N")
    ax_ppi.set_theta_direction(-1) # Clockwise
    ax_ppi.tick_params(axis='both', colors=theme_color)
    ax_ppi.set_rlim(0, max_display_range)
    ax_ppi.set_yticks(np.arange(0, max_display_range + 25, 25))
    ax_ppi.set_yticklabels([f'{r}m' for r in np.arange(0, max_display_range + 25, 25)], 
                           color=theme_color, alpha=0.7)
    ax_ppi.set_xticks(np.deg2rad(np.arange(0, 360, 45)))
    ax_ppi.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'], 
                           color=theme_color, fontsize=10)
    
    # --- Sweep elements ---
    BEAM_WIDTH = np.deg2rad(5)
    sweep_angle = 0
    
    # Wedge for the beam fill
    sweep_wedge = Wedge((0, 0), max_display_range, 0, np.rad2deg(BEAM_WIDTH), 
                        facecolor=theme_color, alpha=0.5, zorder=2)
    ax_ppi.add_patch(sweep_wedge)
    
    # Line for the leading edge (will pulse)
    sweep_line, = ax_ppi.plot([0, sweep_angle], [0, max_display_range], 
                              color=DEFAULT_LINE_COLOR, linewidth=DEFAULT_LINE_WIDTH, 
                              alpha=1.0, zorder=3)
    
    # Target blips (Scatter plot)
    blips_scatter = ax_ppi.scatter([], [], s=[], color=theme_color, marker='o', 
                                   alpha=1.0, zorder=5, edgecolors='white', linewidths=0.5)
    
    # Remove the tight_layout call since we only have one plot now.
    
    # === SIMULATION LOOP ===
    frame_count = 0
    
    try:
        while plt.get_fignums():
            start_time = time.time()
            
            # --- Dynamic Target Update (Simulated Reality) ---
            if frame_count == 30:
                print("\n[EVENT] New target appears at 35m moving fast!")
                current_ranges.append(35.0)
                velocities.append(15.0)
                rcs.append(0.7)
            
            if frame_count == 80:
                print("[EVENT] Target slows down and changes direction.")
                if len(velocities) > 1:
                     velocities[1] = 2.0
            
            # Update target positions
            current_ranges = [r + v * frame_time_step for r, v in zip(current_ranges, velocities)]
            
            # Boundary handling (Targets bounce back)
            for i in range(len(current_ranges)):
                if current_ranges[i] < 5:
                    current_ranges[i] = 5
                    velocities[i] = abs(velocities[i])
                elif current_ranges[i] > radar.R_max * 0.95:
                    current_ranges[i] = radar.R_max * 0.95
                    velocities[i] = -abs(velocities[i])
            
            # --- Radar Processing ---
            tx, rx = radar.simulate_targets(current_ranges, velocities, rcs)
            range_fft, _ = radar.range_fft(tx, rx)
            detected_indices = radar.cfar_detection(range_fft)
            detected_ranges = [range_bins_half[i] for i in detected_indices]
            
            # Flag for instantaneous pulse effect
            is_detected_in_frame = len(detected_ranges) > 0
            
            # --- PPI Sweep Rotation ---
            sweep_angle = (sweep_angle + np.deg2rad(5)) % (2 * np.pi)
            
            
            # --- TARGET BLIP PERSISTENCE & VELOCITY ASSOCIATION LOGIC ---
            nearest_target_info = None 
            
            # 1. Decay the alpha of all existing blips
            blips_to_remove = []
            for r_id, blip_data in list(target_blips.items()):
                blip_data['alpha'] -= BLIP_FADE_RATE
                if blip_data['alpha'] < BLIP_MIN_ALPHA:
                    blips_to_remove.append(r_id)
            
            for k in blips_to_remove:
                del target_blips[k]
            
            # 2. Process current detections 
            if detected_ranges:
                for i, r_id in enumerate(detected_indices):
                    current_r = detected_ranges[i]
                    
                    # --- Match detected range to a simulated target for velocity info ---
                    current_velocity = 0.0
                    min_range_diff = float('inf')
                    
                    for sim_idx, sim_r in enumerate(current_ranges):
                         diff = abs(current_r - sim_r)
                         if diff < min_range_diff and diff < radar.range_res * 0.5:
                             min_range_diff = diff
                             current_velocity = velocities[sim_idx]
                             break

                    # --- Blip Management ---
                    if r_id not in target_blips:
                        # NEW target detected: Initialize with fixed azimuth and derived velocity
                        target_blips[r_id] = {'azimuth': sweep_angle, 
                                              'range': current_r,
                                              'velocity': current_velocity,
                                              'alpha': 1.0}
                    else:
                        # EXISTING target detected: Refresh properties
                        target_blips[r_id]['range'] = current_r
                        target_blips[r_id]['velocity'] = current_velocity
                        target_blips[r_id]['alpha'] = 1.0 # Refresh alpha (brighten blip)
                        
                    # Update nearest target info (used only for internal logging/status calculation)
                    if nearest_target_info is None or current_r < nearest_target_info['range']:
                        nearest_target_info = {'range': current_r, 'velocity': current_velocity}

            # 3. Collect all current (visible) blips for plotting
            new_azimuths, new_ranges, new_sizes, new_alphas = [], [], [], []
            for blip_data in target_blips.values():
                
                new_azimuths.append(blip_data['azimuth'])
                new_ranges.append(blip_data['range'])
                new_alphas.append(blip_data['alpha']) 
                
                # SIZING MODIFIED: Size based on velocity
                v_mag = abs(blip_data.get('velocity', 0.0))
                blip_size = 60 + 90 * (v_mag / radar.V_max) 
                new_sizes.append(blip_size)
                
            # Update the scatter plot data
            theme_rgb = mcolors.to_rgb(theme_color)
            new_colors = [theme_rgb + (a,) for a in new_alphas]
            blips_scatter.set_offsets(np.c_[new_azimuths, new_ranges])
            blips_scatter.set_sizes(new_sizes)
            blips_scatter.set_color(new_colors)
            
            # --- PULSING SWEEP LINE UPDATE ---
            if is_detected_in_frame:
                sweep_line.set_color(PULSE_LINE_COLOR)
                sweep_line.set_linewidth(PULSE_LINE_WIDTH)
                sweep_wedge.set_alpha(0.8) # Make wedge slightly brighter
            else:
                sweep_line.set_color(DEFAULT_LINE_COLOR)
                sweep_line.set_linewidth(DEFAULT_LINE_WIDTH)
                sweep_wedge.set_alpha(0.5) # Default wedge transparency
            
            # Update Sweep Wedge and Line position
            sweep_angle_deg = np.rad2deg(sweep_angle)
            beam_width_deg = np.rad2deg(BEAM_WIDTH)
            sweep_wedge.set_theta1(sweep_angle_deg - beam_width_deg)
            sweep_wedge.set_theta2(sweep_angle_deg)
            sweep_line.set_xdata([sweep_angle, sweep_angle])
            
            # --- Status Update ---
            status_text = 'TARGET DETECTED' if is_detected_in_frame else 'SCANNING'
            status_color = PULSE_LINE_COLOR if is_detected_in_frame else 'white'
            
            # Update PPI title
            ax_ppi.set_title(f"FMCW Radar PPI - Status: {status_text}", 
                            color=status_color, fontsize=16, y=1.05) # Increased font size and offset title
            
            # Draw and pause
            fig.canvas.draw()
            fig.canvas.flush_events()
            
            elapsed_time = time.time() - start_time
            pause_time = max(0.01, frame_time_step - elapsed_time)
            plt.pause(pause_time)
            
            frame_count += 1
            
    except Exception as e:
        print(f"Simulation error: {e}")
    finally:
        plt.ioff()
        plt.close()
        print("Simulation completed.")

if __name__ == "__main__":
    main()
