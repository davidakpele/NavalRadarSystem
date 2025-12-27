import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import numpy.fft as fft

class FMCW_Radar_Simulator:
    def __init__(self):
        self.B = 200e6  # Bandwidth: 200 MHz
        self.T = 50e-6  # Chirp duration: 50 μs
        self.fc = 24e9  # Carrier frequency: 24 GHz
        self.fs = 2e6   # Sampling rate: 2 MHz
        self.c = 3e8    # Speed of light
        
    def simulate_targets(self, ranges, velocities, rcs):
        """Simulate multiple targets with range, velocity, and radar cross-section"""
        # Time vector
        t = np.arange(0, self.T, 1/self.fs)
        num_samples = len(t)
        
        # Transmit chirp
        tx_chirp = np.exp(1j * 2 * np.pi * (self.fc * t + (self.B/(2*self.T)) * t**2))
        
        # Initialize received signal
        rx_signal = np.zeros(num_samples, dtype=complex)
        
        # Add each target's reflection
        for range, vel, rc in zip(ranges, velocities, rcs):
            # Time delay considering velocity
            delay = 2 * (range + vel * t) / self.c
            # Received chirp with attenuation and phase shift
            attenuation = np.sqrt(rc) / (range**2)  # Simple RCS and range model
            rx_chirp = attenuation * np.exp(1j * 2 * np.pi * 
                         (self.fc * (t - delay) + (self.B/(2*self.T)) * (t - delay)**2))
            rx_signal += rx_chirp
        
        # Add noise
        noise_power = 0.01
        rx_signal += np.sqrt(noise_power/2) * (np.random.randn(num_samples) + 
                       1j * np.random.randn(num_samples))
        
        return tx_chirp, rx_signal, t
    
    def range_fft(self, tx_signal, rx_signal):
        """Calculate range FFT"""
        # Mix transmit and receive signals
        mixed = tx_signal * np.conj(rx_signal)
        
        # Window and FFT
        window = np.hanning(len(mixed))
        range_fft = fft.fft(mixed * window)
        
        # Calculate range bins
        range_bins = (np.arange(len(range_fft)) * self.c) / (2 * self.B)
        
        return range_fft, range_bins

    def doppler_processing(self, ranges, velocities, rcs, num_chirps=64):
        """Simulate Doppler processing for velocity measurement"""
        # Generate multiple chirps
        range_doppler_map = np.zeros((256, num_chirps), dtype=complex)
        
        for chirp_idx in range(num_chirps):
            # Simulate small time progression for Doppler
            time_offset = chirp_idx * self.T
            ranges_doppler = [r + v * time_offset for r, v in zip(ranges, velocities)]
            
            tx, rx, _ = self.simulate_targets(ranges_doppler, velocities, rcs)
            range_fft, _ = self.range_fft(tx, rx)
            range_doppler_map[:, chirp_idx] = range_fft[:256]
        
        # Doppler FFT
        doppler_fft = fft.fftshift(fft.fft(range_doppler_map, axis=1), axes=1)
        
        return doppler_fft

    def cfar_detection(self, range_profile, guard_cells=10, training_cells=20, threshold_factor=1.5):
        """Constant False Alarm Rate target detection"""
        num_cells = len(range_profile)
        detected_targets = []
        power_profile = np.abs(range_profile)**2
        
        for i in range(num_cells):
            if i < guard_cells + training_cells or i >= num_cells - guard_cells - training_cells:
                continue
                
            # Cells before guard region
            leading_cells = power_profile[i-training_cells-guard_cells:i-guard_cells]
            # Cells after guard region  
            trailing_cells = power_profile[i+guard_cells+1:i+guard_cells+training_cells+1]
            
            # Calculate noise floor
            noise_floor = np.mean(np.concatenate([leading_cells, trailing_cells]))
            threshold = threshold_factor * noise_floor
            
            if power_profile[i] > threshold:
                detected_targets.append(i)
        
        return detected_targets

class CompleteRadarPipeline:
    def __init__(self):
        self.radar = FMCW_Radar_Simulator()
        
    def full_processing(self):
        # 1. Simulate radar data
        print("Simulating radar signals...")
        ranges = [12, 35, 67]
        velocities = [8, -5, 15]
        rcs = [1.0, 0.7, 1.5]
        
        tx, rx, t = self.radar.simulate_targets(ranges, velocities, rcs)
        
        # 2. Range processing
        print("Processing range information...")
        range_fft, range_bins = self.radar.range_fft(tx, rx)
        
        # 3. Target detection
        print("Detecting targets...")
        detected_indices = self.radar.cfar_detection(range_fft)
        detected_ranges = [range_bins[i] for i in detected_indices]
        
        # 4. Doppler processing
        print("Processing velocity information...")
        doppler_map = self.radar.doppler_processing(ranges, velocities, rcs)
        
        # 5. Display results
        print("\n=== RADAR DETECTION RESULTS ===")
        print(f"Simulated targets at: {ranges} m")
        print(f"Detected targets at: {[f'{r:.1f}' for r in detected_ranges]} m")
        print(f"Target velocities: {velocities} m/s")
        
        return detected_ranges, doppler_map, range_fft, range_bins, tx, rx, t

def main():
    print("🚀 FMCW Radar Simulation")
    print("=" * 50)
    
    # Create radar simulator
    radar = FMCW_Radar_Simulator()
    
    # Simulate 3 targets at different ranges and velocities
    ranges = [15, 45, 80]  # meters
    velocities = [5, -10, 0]  # m/s
    rcs = [1.0, 0.5, 2.0]  # radar cross-section
    
    print(f"Targets: {ranges} m")
    print(f"Velocities: {velocities} m/s")
    
    # Get signals
    tx, rx, t = radar.simulate_targets(ranges, velocities, rcs)
    range_fft, range_bins = radar.range_fft(tx, rx)
    
    # Plot results
    plt.figure(figsize=(15, 10))
    
    # Plot 1: Chirp signals
    plt.subplot(2, 3, 1)
    plt.plot(t*1e6, np.real(tx[:1000]), label='TX Chirp', linewidth=2)
    plt.plot(t*1e6, np.real(rx[:1000]), label='RX Signal', alpha=0.8)
    plt.xlabel('Time (μs)')
    plt.ylabel('Amplitude')
    plt.legend()
    plt.title('Transmit and Receive Signals')
    plt.grid(True)
    
    # Plot 2: Range profile
    plt.subplot(2, 3, 2)
    n_half = len(range_fft) // 2
    plt.plot(range_bins[:n_half], 20*np.log10(np.abs(range_fft[:n_half]) + 1e-10))
    plt.xlabel('Range (m)')
    plt.ylabel('Power (dB)')
    plt.title('Range Profile - Detected Targets')
    plt.grid(True)
    
    # Plot 3: CFAR detection
    plt.subplot(2, 3, 3)
    detected_indices = radar.cfar_detection(range_fft)
    detected_ranges = [range_bins[i] for i in detected_indices]
    
    range_power_db = 20*np.log10(np.abs(range_fft[:n_half]) + 1e-10)
    plt.plot(range_bins[:n_half], range_power_db, label='Range Profile')
    plt.scatter(detected_ranges, [range_power_db[i] for i in detected_indices], 
                color='red', s=50, zorder=5, label='CFAR Detection')
    plt.xlabel('Range (m)')
    plt.ylabel('Power (dB)')
    plt.title('CFAR Target Detection')
    plt.legend()
    plt.grid(True)
    
    # Plot 4: Range-Doppler map
    plt.subplot(2, 3, 4)
    doppler_map = radar.doppler_processing(ranges, velocities, rcs, num_chirps=32)
    plt.imshow(20*np.log10(np.abs(doppler_map) + 1e-10), 
               aspect='auto', 
               extent=[-25, 25, 0, 100],  # velocity vs range
               cmap='hot')
    plt.colorbar(label='Power (dB)')
    plt.xlabel('Velocity (m/s)')
    plt.ylabel('Range (m)')
    plt.title('Range-Doppler Map')
    
    # Plot 5: Signal spectrum
    plt.subplot(2, 3, 5)
    tx_fft = fft.fft(tx)
    rx_fft = fft.fft(rx)
    freq = fft.fftfreq(len(tx), d=1/radar.fs) / 1e6  # Convert to MHz
    
    n_half = len(freq) // 2
    plt.plot(freq[:n_half], 20*np.log10(np.abs(tx_fft[:n_half]) + 1e-10), 
             label='TX Spectrum')
    plt.plot(freq[:n_half], 20*np.log10(np.abs(rx_fft[:n_half]) + 1e-10), 
             label='RX Spectrum', alpha=0.8)
    plt.xlabel('Frequency (MHz)')
    plt.ylabel('Power (dB)')
    plt.title('Frequency Spectrum')
    plt.legend()
    plt.grid(True)
    
    # Plot 6: Mixed signal
    plt.subplot(2, 3, 6)
    mixed = tx * np.conj(rx)
    mixed_fft = fft.fft(mixed)
    plt.plot(range_bins[:n_half], np.abs(mixed_fft[:n_half]))
    plt.xlabel('Range (m)')
    plt.ylabel('Magnitude')
    plt.title('Beat Frequency Spectrum')
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()
    
    # Print detection results
    print(f"\n📊 Detection Results:")
    print(f"Detected targets at ranges: {[f'{r:.1f}' for r in detected_ranges]} meters")
    
    # Run complete pipeline
    print("\n" + "="*50)
    print("Running Complete Pipeline...")
    print("="*50)
    
    pipeline = CompleteRadarPipeline()
    detected_ranges, doppler_map, range_fft, range_bins, tx, rx, t = pipeline.full_processing()

if __name__ == "__main__":
    main()