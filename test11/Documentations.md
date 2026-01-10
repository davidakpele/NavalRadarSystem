# 🎯 Advanced Naval Acoustic Radar System - Real-Time Multi-Mode Detection

I'm excited to share my latest project: a **sophisticated naval acoustic radar simulation** that combines real-time audio processing, advanced signal analysis, and tactical naval operations in an interactive visualization system!

## 🚀 What I Built

A comprehensive real-time acoustic detection and tracking system that simulates professional naval radar operations with **live audio input**, multiple detection modes, and advanced tactical analysis capabilities.

## ✨ Core Features & Technologies

### 🎧 Real-Time Audio Processing & Analysis
- **Live microphone input** with 44.1kHz sampling rate
- **FFT (Fast Fourier Transform)** for frequency domain analysis
- **Stereo directional detection** using cross-correlation
- **Adaptive noise gating** with configurable thresholds
- **Multi-band frequency filtering** (lowpass, highpass, bandpass)
- **Variable gain control** for signal amplification
- **Signal-to-Noise Ratio (SNR) analysis** with quality metrics

### 🎯 Multi-Mode Detection System
Implemented **5 distinct radar modes**, each with unique characteristics:

1. **PASSIVE Mode** - Stealth listening with 60° detection arc
2. **ACTIVE SONAR** - Pulse-echo ranging with 2x range multiplier and true distance calculation
3. **WIDE BEAM** - Broad coverage (120° arc) for surveillance
4. **NARROW BEAM** - Focused sector scanning (30° arc) with manual steering
5. **360° OMNI** - All-direction simultaneous monitoring

### 🎨 Advanced Visualization
- **Real-time radar display** with configurable range rings (5-100 NM)
- **Dynamic sweep lines** with fade trails
- **Target trails** showing movement history
- **Velocity vectors** with directional indicators
- **Predicted position tracking** (5-step prediction algorithm)
- **3D visualization mode** with perspective projection
- **CRT effect** with scanlines and vignette
- **Multiple color themes** (Green, Blue, Amber, Red, Custom)
- **Zoom and pan controls** (0.5x to 2.0x)

### 🎵 Comprehensive Sound System
- **Synthetic sound generation** using NumPy waveforms
- **Stereo audio** with independent channel processing
- **Context-aware sound effects**:
  - Radar sweep sounds (mode-specific)
  - Sonar pings and echoes
  - Target detection alerts (threat-based)
  - UI interaction feedback
  - Warning alarms for hostile targets
- **Volume control** and selective muting options
- **Ambient background** with realistic radar room atmosphere

### 🔍 Target Classification & Tracking

**AI-Powered Classification System:**
- **12+ vessel types** with acoustic signatures:
  - Surface: Merchant vessels, warships, fast attack craft, fishing boats
  - Subsurface: Nuclear/diesel submarines, torpedoes, UUVs
  - Biological: Whales, dolphins, fish schools
  - Environmental: Seismic surveys, weather noise

**Classification Features:**
- **Frequency profile matching** (5Hz - 20kHz range)
- **Speed correlation** (1-70 knots)
- **Modulation pattern analysis** (steady, pulsed, irregular)
- **Harmonic content detection**
- **Multi-factor scoring algorithm** with confidence levels
- **Real-time classification updates** based on acoustic data

### 🎖️ Advanced Tactical Features

**Bearing Rate Tracker:**
- **Degrees per minute** calculation
- **Crossing prediction** (ahead/astern, port/starboard)
- **Time to crossing** estimation
- **Aspect determination** (bow, beam, stern, quarter)
- **Bearing drift visualization** with trend analysis
- **Rapid bearing change alerts** for collision risk

**Closest Point of Approach (CPA) Analysis:**
- **CPA distance calculation** with danger zones (2 NM alert threshold)
- **Time to CPA** in minutes
- **Closing rate analysis** with classifications:
  - Rapid Close (>15 knots)
  - Closing (5-15 knots)
  - Steady (-5 to +5 knots)
  - Opening (<-5 knots)
- **Visual CPA markers** on radar display
- **Color-coded warnings** based on threat level

**Torpedo Detection & Defense:**
- **High-speed target analysis** (25-70+ knots)
- **Torpedo signature matching** with probability scoring
- **Impact prediction** with countdown timers
- **Evasion recommendations** (course changes, speed adjustments)
- **Acoustic decoy deployment** with cooldown management
- **Multi-torpedo tracking** with status monitoring
- **Real-time alerts** with flashing warnings

**Signal-to-Noise Ratio (SNR) Analysis:**
- **Real-time SNR calculation** (signal level - background noise)
- **Quality ratings** (Excellent, Good, Fair, Poor, Very Poor)
- **Detection confidence scoring** (0-100%)
- **Classification quality assessment**
- **SNR trend analysis** (improving/degrading/steady)
- **Historical SNR graphing** with bar charts

### 📊 Data Analytics & Intelligence

**Statistical Analysis:**
- **Target trajectory analysis** with polynomial fitting
- **Collision prediction** using linear extrapolation
- **Threat distribution tracking** (hostile, unknown, neutral, friendly)
- **Activity level monitoring** (0-100% scale)
- **Velocity statistics** (average, maximum)
- **Heat map generation** (360° bearing × 100 range bins)

**Mission Scenario System:**
- **Pre-programmed scenarios**: Training, Coastal Patrol, Search & Rescue
- **Scripted events** with timed triggers
- **Objective tracking** with progress indicators
- **Custom scenario creation** capability
- **Auto-spawning targets** based on mission parameters

### 💾 Recording & Data Export

**Session Recording:**
- **Multi-format capture**:
  - Video frame buffering (up to 1 minute at 60 FPS)
  - Audio WAV export (44.1kHz stereo)
  - JSON session metadata
  - CSV target history
- **Atomic file operations** for data integrity
- **Persistent chat history** across sessions
- **Selective recording** (audio-only, video-only options)

**Export Capabilities:**
- **CSV export** with target parameters (bearing, range, velocity, threat)
- **JSON export** with complete target data structures
- **Screenshot capture** with timestamp naming
- **Analytics export** (statistics, trajectories, heat maps)
- **Torpedo alert logs** with detailed incident reports

### 🖥️ User Interface & Controls

**Draggable Panel System (12 panels):**
1. Detection Mode Selector
2. System Status Monitor
3. Own Ship Data
4. Tracked Targets List
5. Acoustic Sensor Display
6. Recording Controls
7. Analytics Dashboard
8. Mission Control
9. Target Classification
10. Bearing Rate Tracker
11. SNR Analysis
12. Torpedo Defense

**Panel Features:**
- **Click-and-drag repositioning**
- **Collapsible interface** to reduce screen clutter
- **Real-time data updates** at 60 FPS
- **Color-coded indicators** for status
- **Contextual information** based on selected targets

### ⚙️ Advanced Configuration

**Adjustable Parameters:**
- Range settings (5-100 nautical miles)
- Gain control (0.1x - 3.0x amplification)
- Noise gate threshold (0.0 - 0.9)
- Target size filtering (intensity thresholds)
- Brightness control (30% - 100%)
- Frequency filters (lowpass/highpass/bandpass)
- Zoom levels (0.5x - 2.0x)
- Audio volume (0% - 100%)

## 🛠️ Technical Implementation

### Technology Stack:
- **Core**: Python with Pygame for rendering
- **Audio**: SoundDevice for real-time capture, NumPy for DSP
- **Signal Processing**: SciPy for FFT, filtering, envelope detection
- **Data Structures**: Dataclasses, Deques, Dictionaries
- **Mathematics**: NumPy for vector operations, trigonometry
- **File I/O**: JSON, CSV, WAV formats
- **Threading**: Callback-based audio processing

### Key Algorithms:
- **Cross-correlation** for directional audio analysis
- **FFT** for frequency spectrum analysis
- **Butterworth filters** for frequency band isolation
- **Hilbert transform** for envelope detection
- **Polynomial fitting** for trajectory prediction
- **Linear extrapolation** for CPA calculation
- **Multi-factor scoring** for classification

### Performance Optimizations:
- **Circular buffers** (deques) for efficient memory management
- **Frame-rate limiting** at 60 FPS
- **Selective rendering** based on visibility
- **Audio chunk processing** (1024-sample blocks)
- **Lazy evaluation** of analytics
- **Efficient collision detection** using spatial hashing

## 📈 System Capabilities

### Real-Time Performance:
- **60 FPS** sustained rendering
- **<20ms** audio latency
- **Unlimited targets** (tested with 50+ simultaneous)
- **1-second** target detection cooldown
- **Sub-degree** bearing accuracy
- **0.1 NM** range precision

### Detection Range:
- **Passive**: 50 NM baseline
- **Active Sonar**: 100 NM (2x multiplier)
- **Frequency Range**: 5 Hz - 20 kHz
- **Angular Resolution**: 1° (configurable)

## 💡 Use Cases & Applications

This system demonstrates proficiency in:
- **Real-time signal processing** and audio analysis
- **Multi-threaded programming** for concurrent I/O
- **Interactive visualization** with complex UI
- **State management** in real-time systems
- **Data persistence** and export workflows
- **Algorithm implementation** (FFT, correlation, prediction)
- **Game development** techniques in simulation
- **Naval tactical operations** simulation

Potential applications:
- **Maritime training simulators**
- **Acoustic research** and analysis tools
- **Audio visualization** systems
- **Threat detection** algorithm development
- **Sonar operator training**
- **Marine wildlife monitoring**

## 🎓 What I Learned

Building this project taught me:
- Advanced **digital signal processing** (FFT, filtering, correlation)
- **Real-time audio capture** and analysis pipelines
- **Complex state management** in interactive systems
- **Multi-mode system design** with configurable behaviors
- **Tactical naval operations** and sonar principles
- **Data-driven classification** algorithms
- **Performance optimization** for real-time constraints
- **Professional UI/UX** for technical applications
- **Comprehensive error handling** in audio systems

## 🔮 Future Enhancements

Planning to add:
- **Machine learning** classification (neural networks)
- **Multi-target tracking** with Kalman filters
- **Passive ranging** using triangulation
- **Water propagation modeling** (thermoclines, reflections)
- **Network multiplayer** for multi-ship coordination
- **Historical replay** with scrubbing
- **VR integration** for immersive operation
- **Real sonar hardware** interface

## 🎯 Key Achievements

✅ **Real-time audio processing** at 44.1kHz with <20ms latency  
✅ **12+ vessel classifications** with AI-powered signature matching  
✅ **5 detection modes** with unique tactical properties  
✅ **Torpedo defense system** with countermeasure deployment  
✅ **CPA analysis** with collision prediction  
✅ **Complete recording suite** (video, audio, data)  
✅ **12-panel draggable UI** with professional presentation  
✅ **60 FPS sustained** performance with 50+ targets  
✅ **Comprehensive sound system** with 8+ dynamic effects  
✅ **Mission scripting** with scenario management  

---

**Technologies:** Python • Pygame • NumPy • SciPy • Digital Signal Processing • Real-Time Audio • FFT Analysis • State Machines • Data Visualization • Multi-Threading

**Skills Demonstrated:** Real-Time Systems • Signal Processing • UI/UX Design • Algorithm Implementation • Performance Optimization • Data Analytics • Audio Engineering • Military Simulation

#Python #SignalProcessing #AudioEngineering #Pygame #RealTimeProcessing #DataVisualization #MachineLearning #SoftwareDevelopment #NavalSimulation #DSP #FFT #SonarTechnology #GameDev #TechInnovation

---

**Want to try it?** The system runs on any computer with a microphone - just speak, play music, or make sounds and watch the radar detect and classify acoustic signatures in real-time!

🔗 *Open to collaboration on similar projects or discussing the technical implementation!*
