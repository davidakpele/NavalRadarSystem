# Advanced Naval Acoustic Radar System v2.0

## 📋 Project Overview

An immersive, real-time naval acoustic radar simulation system that combines audio analysis with visual radar displays to detect and track maritime targets. The system simulates various naval radar detection modes, processes live audio input for target detection, and provides a comprehensive user interface for tactical analysis.

## 🎯 Core Features

### 1. **Multi-Mode Detection System**
- **Passive Mode**: Stealth listening with 60° detection arc
- **Active Sonar**: Pulse echo ranging with 45° arc and true distance calculation
- **Wide Beam**: Broad 120° coverage for situational awareness
- **Narrow Beam**: Focused 30° sector for high-accuracy tracking
- **Omni 360**: 360° coverage with pulsing circular detection

### 2. **Audio Processing Engine**
- Real-time audio stream analysis (44.1kHz, stereo)
- FFT frequency analysis for sound classification
- Stereo correlation for directional bearing calculation
- Adjustable gain control, noise gates, and frequency filters
- Live audio input processing for target detection

### 3. **Target Management System**
- Intelligent target creation and updating
- Velocity and angular velocity calculations
- Position history tracking with visual trails
- Future position prediction algorithms
- Threat level classification (Hostile, Unknown, Friendly, Neutral)

### 4. **Immersive Sound System**
- Synthetic radar sweep sounds with frequency modulation
- Target detection sounds based on threat level
- Active sonar pulse and echo simulation
- Ambient radar room noise with stereo effects
- UI interaction sounds and mode change feedback
- Configurable sound controls (detection sounds, sweep sounds, ambient)

### 5. **Data Recording & Export**
- Session recording with metadata tracking
- Frame buffering for video recording
- Audio recording with WAV export
- Target event logging with CSV/JSON export
- Heatmap data generation for analysis

### 6. **Visual Display System**
- Interactive radar display with range rings
- Compass rose and directional indicators
- Adjustable zoom levels (0.5x to 2.0x)
- Multiple color themes (Green, Blue, Amber, Red, Custom)
- CRT screen effect option
- Brightness and contrast controls

### 7. **User Interface**
- Draggable, collapsible control panels
- Real-time system status monitoring
- Own ship data display (heading, speed, position, depth)
- Tracked targets panel with detailed information
- Acoustic sensor visualization
- Recording controls and status

## 🎮 Control System

### Keyboard Shortcuts

#### **Detection Modes**
- `1-5`: Switch between detection modes
- `SPACE`: Sonar pulse (Active mode) / Pause toggle
- `←/→`: Adjust narrow beam angle

#### **Sound Controls**
- `V`: Toggle mute/unmute
- `↑/↓`: Volume up/down
- `L`: Toggle detection sounds
- `K`: Toggle sweep sounds

#### **Recording & Export**
- `R`: Start/Stop recording session
- `S`: Take screenshot
- `E`: Export targets to CSV
- `J`: Export targets to JSON
- `C`: Clear all targets

#### **Display Controls**
- `T`: Cycle through color themes
- `B/D`: Brightness up/down
- `G`: Toggle grid display
- `O`: Toggle compass display
- `X`: Toggle CRT effect
- `+/-`: Zoom in/out
- `0`: Reset zoom to default
- `[/]`: Decrease/Increase radar range

#### **Audio Processing**
- `,/.`: Gain control down/up
- `F`: Cycle frequency filters (None/Lowpass/Highpass/Bandpass)
- `N/M`: Noise gate up/down
- `Y/U`: Target size filter down/up

#### **System**
- `H`: Display help screen
- `ESC`: Exit application

### Mouse Controls
- **Left Click**: Select targets
- **Mouse Wheel**: Zoom in/out
- **Drag Panel Title Bars**: Reposition control panels
- **Click Collapse Button**: Minimize/expand panels

## 🏗️ System Architecture

### **Core Components**

1. **SoundSystem Class**
   - Manages all audio synthesis and playback
   - Creates synthetic radar sounds programmatically
   - Handles sound effect triggering based on system events

2. **Target Class**
   - Represents individual detected targets
   - Tracks position, velocity, threat level, and detection history
   - Handles fading and prediction algorithms

3. **TargetManager Class**
   - Central manager for all active targets
   - Handles target creation, updating, and removal
   - Manages target selection and collision detection

4. **SessionRecorder Class**
   - Records all system activity
   - Captures frames, audio, and target events
   - Exports data in multiple formats

5. **ModeConfig System**
   - Defines parameters for each detection mode
   - Controls detection arcs, range multipliers, and accuracy
   - Manages mode-specific visual and audio characteristics

6. **Panel System**
   - Interactive, draggable UI panels
   - Collapsible sections for efficient screen space use
   - Real-time data visualization

### **Audio Processing Pipeline**
1. Live audio input capture
2. Stereo-to-mono conversion
3. Frequency filtering (if enabled)
4. FFT analysis for frequency detection
5. Stereo correlation for bearing calculation
6. Sound classification based on frequency ranges
7. Intensity calculation for target creation

### **Visual Rendering Pipeline**
1. Radar background with range rings
2. Grid and compass overlay
3. Sweep line drawing (mode-specific)
4. Target rendering with trails and velocity vectors
5. UI panel rendering
6. Status overlay

## 📊 Data Management

### **Recording Capabilities**
- **Session Recording**: Complete system state capture
- **Video Frames**: Screen capture for later review
- **Audio Samples**: Raw audio data recording
- **Event Logging**: Target detections and mode changes

### **Export Formats**
- **CSV**: Tabular target data for spreadsheet analysis
- **JSON**: Structured data for programmatic processing
- **Heatmaps**: Frequency and bearing density visualization
- **Session Reports**: Comprehensive activity summaries

### **Storage Organization**
- `recordings/`: Audio and video recordings
- `sessions/`: Session data and metadata
- `screenshots/`: Captured screen images
- `exports/`: Exported CSV/JSON files

## 🎨 Visual Themes

Five distinct color themes optimized for different lighting conditions:

1. **Green**: Classic radar green (default)
2. **Blue**: Deep ocean blue
3. **Amber**: Warm amber for low-light
4. **Red**: High-contrast red alert
5. **Custom**: Purple/magenta aesthetic

## 🛠️ Technical Specifications

### **Requirements**
- Python 3.8+
- Pygame 2.0+
- NumPy & SciPy for signal processing
- SoundDevice for audio I/O

### **Performance**
- Target: 60 FPS
- Audio: 44.1kHz sample rate
- Radar: 350px radius display
- Memory: Configurable frame buffering

### **Compatibility**
- Cross-platform (Windows, macOS, Linux)
- Adjustable window sizes (resizable)
- Fullscreen mode support

## 🎯 Use Cases

### **Training & Simulation**
- Naval operations training
- Sonar operator practice
- Tactical decision-making exercises

### **Educational**
- Radar and sonar principles demonstration
- Audio signal processing visualization
- Real-time system design example

### **Development & Testing**
- Algorithm development for target tracking
- Audio processing technique experimentation
- UI/UX design for complex systems

## 🔧 Configuration Options

### **System Settings**
- Radar range: 5-100 nautical miles
- Gain control: 0.1x to 3.0x
- Noise gate: 0.0 to 0.9 threshold
- Zoom level: 0.5x to 2.0x

### **Visual Settings**
- Grid display toggle
- Compass display toggle
- CRT effect toggle
- Brightness: 0.3 to 1.0

### **Audio Settings**
- Frequency filters: None/Lowpass/Highpass/Bandpass
- Target size filtering
- Individual sound effect toggles

## 📈 Advanced Features

### **Target Intelligence**
- Automatic threat classification
- Velocity vector calculation
- Trajectory prediction
- Collision detection

### **Audio Intelligence**
- Real-time frequency analysis
- Sound type classification
- Bearing calculation from stereo audio
- Confidence scoring for detections

### **System Intelligence**
- Mode-specific detection algorithms
- Context-aware audio processing
- Adaptive threshold management
- Performance-optimized rendering

## 🚀 Getting Started

### **Quick Start**
1. Install dependencies: `pip install pygame numpy scipy sounddevice`
2. Run: `python main.py`
3. Press `H` for help
4. Connect audio input for live detection

### **First Steps**
1. Start with **Passive Mode** (press `1`)
2. Speak into microphone to create targets
3. Switch to **Active Sonar** (press `2`) for precise ranging
4. Use `R` to start recording your session
5. Export data with `E` or `J`

## 📝 Notes

- **Audio Input Required**: The system requires a microphone or audio input device for target detection
- **Performance**: May require tuning of audio processing parameters for optimal detection
- **Customization**: All color schemes and detection parameters are configurable via code
- **Extensibility**: Modular design allows for easy addition of new detection modes or features

## 🔮 Future Enhancements

Planned features for future versions:
- Network multiplayer mode
- Additional sensor types
- Enhanced target classification
- 3D visualization mode
- Advanced data analytics
- Mission scenario scripting

---

**Developed for educational and simulation purposes** – This system demonstrates principles of radar/sonar operation, real-time audio processing, and complex system design in an interactive, engaging format.