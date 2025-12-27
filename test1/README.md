## Project Overview

The Acoustic Naval Radar is a high-performance Python application designed to run entirely on local hardware. It utilizes Digital Signal Processing (DSP) to analyze incoming stereo audio signals, calculate the direction of the sound source, and display that data on a military-grade **Plan Position Indicator (PPI)** radar scope.

---

## Key Features

### 1. Real-Time Acoustic Tracking

* **Direction of Arrival (DOA):** Uses the Time Difference of Arrival (TDOA) method between two microphone channels to determine the angle of a sound source.
* **Signal Intensity Mapping:** The distance of a "blip" from the center of the radar represents the volume/intensity of the detected noise.
* **Automatic Decay:** Detected targets (blips) naturally fade over time, simulating the phosphor afterglow of historical CRT radar screens.

### 2. Naval Interface (UI/UX)

* **Rotating Magnetron Sweep:** A continuous 360-degree visual sweep that "discovers" noise targets as it passes their calculated bearing.
* **Dynamic Data Panel:** A side-mounted telemetry box showing live status, signal intensity, and bearing in degrees.
* **Grid System:** Standard circular range rings and 30-degree bearing increments for precise navigation.

### 3. Hardware Optimization

* **GPU Accelerated:** Uses Pygame’s rendering engine to leverage your **NVIDIA RTX GPU** for smooth alpha-blending and high frame rates.
* **Multi-Core Processing:** Offloads audio processing to the **Ryzen 7000** series CPU to ensure zero-latency feedback.

---

## How It Works

### The Physics of Detection

The system relies on the fact that sound reaches two different microphones at slightly different times if the source is not perfectly centered.

1. **Audio Capture:** The system captures 1024 samples of audio at 44.1kHz.
2. **Cross-Correlation:** It compares the left and right waveforms. If the sound hits the left mic first, a "delay" is calculated.
3. **Trigonometric Mapping:** That delay is converted into a bearing (angle).
4. **Radar Rendering:** When the visual sweep reaches that specific angle, a green blip is rendered on the screen.

### The Display Layout

The interface follows standard maritime radar conventions:

* **Heading:** The top of the screen represents 000° (North/Bow).
* **Range Rings:** Four concentric circles used to estimate the "distance" (volume) of the sound.
* **Sweep Trail:** A fading gradient behind the sweep line to provide visual continuity.

---

## System Requirements

### Hardware

* **Processor:** AMD Ryzen 7000 Series (or equivalent high-speed multi-core CPU).
* **Graphics:** NVIDIA GeForce RTX Series (for smooth UI rendering).
* **Audio:** A **Stereo Microphone** setup is required. The system needs two distinct channels (Left/Right) to calculate direction. Integrated "Dual Array" microphones on Lenovo laptops are typically compatible.

### Software

* **Python 3.11+**
* **Libraries:** * `Pygame`: Handles the radar interface and window management.
* `Numpy` & `Scipy`: Perform the complex mathematical correlation for sound detection.
* `Sounddevice`: Provides the bridge between Python and your Windows audio drivers.



---

## Configuration & Calibration

* **Sensitivity:** The detection threshold can be tuned to ignore background hum (like laptop fans) while focusing on louder transient noises (like voices or knocks).
* **Sweep Speed:** The rotation speed can be adjusted to match the "refresh rate" desired for the specific environment.
* **Visual Persistence:** The time it takes for a target to disappear can be increased for long-term monitoring or decreased for high-activity environments.

---

## Troubleshooting

* **No Directional Movement:** Ensure the microphone is not set to "Mono" in Windows Sound Settings.
* **Flickering:** Ensure the RTX drivers are up to date and the power plan is set to "High Performance."
* **TypeError on Blit:** Usually caused by non-integer coordinates; ensure all math results are rounded to the nearest pixel before rendering.

**Would you like me to create a "Log" feature that saves the coordinates of every detected noise to a text file for later review?**