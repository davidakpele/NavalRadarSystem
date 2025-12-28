# Advanced Naval Acoustic Radar System v2.0

## 📋 Project Overview

A sophisticated naval radar simulation and acoustic analysis system built with Python and Pygame. This interactive application simulates various naval radar modes, processes real-time audio input for target detection, and provides advanced data analytics with mission scenario scripting.

## 🎯 Core Features

### 1. **Multi-Mode Detection System**
- **PASSIVE Mode**: Stealth listening with basic detection capabilities
- **ACTIVE SONAR**: Pulse echo ranging for accurate distance measurement
- **WIDE BEAM**: Broad coverage with reduced accuracy
- **NARROW BEAM**: Focused sector scanning for precision
- **360° OMNI**: All-direction detection with range limitations

### 2. **Real-Time Audio Processing**
- Live microphone input analysis (44.1kHz, stereo)
- FFT-based frequency spectrum analysis
- Sound classification by frequency ranges
- Stereo angle detection for directional audio
- Configurable filters (lowpass, highpass, bandpass)

### 3. **Advanced Visualization**
- **2D Radar Display**: Traditional circular radar with range rings and compass
- **3D Visualization Mode**: Perspective view with depth perception
- **Target Tracking**: Real-time target movement with velocity vectors
- **Trail Effects**: Visual history of target movements
- **CRT Effect**: Retro monitor simulation option

### 4. **Target Management System**
- Automatic target creation and updating
- Threat level classification (Hostile, Unknown, Neutral, Friendly)
- Velocity and trajectory calculation
- Collision detection and prediction
- Target fading for stale contacts

### 5. **Data Analytics & Recording**
- **Session Recording**: Capture full radar sessions with timestamps
- **Target History**: Log all detection events with metadata
- **Heatmap Generation**: Visualize target activity patterns
- **Trajectory Analysis**: Predict movement patterns
- **Collision Prediction**: Identify potential conflicts

### 6. **Mission Scenario System**
- **Pre-built Scenarios**: Training, Coastal Patrol, Search & Rescue
- **Custom Scenario Creation**: User-defined mission scripting
- **Timed Events**: Automatic target spawning and messages
- **Objective Tracking**: Mission progress monitoring

### 7. **Sound System**
- **Synthetic Sound Generation**: Procedurally created radar sounds
- **Context-Aware Audio**: Different sounds for different events
- **Volume Control**: Master volume and individual sound adjustments
- **Sound Categories**:
  - Radar sweeps
  - Sonar pings and echoes
  - Target detection alerts
  - UI interaction sounds
  - Ambient background noise

### 8. **User Interface**
- **Draggable Panels**: Fully customizable interface layout
- **Collapsible Sections**: Space-efficient information display
- **Real-time Status**: System statistics and performance metrics
- **Color Themes**: Multiple visual themes (Green, Blue, Amber, Red, Custom)

## 🎮 Controls & Interaction

### Keyboard Shortcuts:
- **1-5**: Switch detection modes
- **R**: Start/Stop session recording
- **S**: Take screenshot
- **E/J**: Export data to CSV/JSON
- **Space**: Sonar pulse (Active mode) / Pause
- **Arrow Keys**: Navigate narrow beam
- **T**: Cycle color themes
- **H**: Show help menu
- **ESC**: Exit application

### Mouse Controls:
- **Left Click**: Select targets
- **Drag**: Move UI panels
- **Mouse Wheel**: Zoom in/out radar view
- **Panel Controls**: Collapse/expand panels with ± buttons

## 📊 Data Management

### Export Formats:
- **CSV**: Tabular target data for spreadsheet analysis
- **JSON**: Structured data for programmatic processing
- **Session Files**: Complete recording sessions with metadata

### File Structure:
- `/sessions/`: Complete session recordings
- `/screenshots/`: Captured radar displays
- `/exports/`: Data exports in various formats
- `/recordings/`: Audio and video recordings

## 🎨 Visual Features

### Display Options:
- **Brightness Control**: Adjust display intensity
- **Grid Toggle**: Show/hide radar grid lines
- **Compass Display**: Nautical direction indicators
- **Zoom Levels**: 0.5x to 2.0x magnification
- **Range Settings**: 5-100 nautical mile scale

### Target Visualization:
- **Shape Coding**: Different shapes for threat levels
- **Color Coding**: Color-based threat identification
- **Trail Lines**: Movement history visualization
- **Velocity Vectors**: Direction and speed indicators
- **Prediction Lines**: Future position estimation

## 🔧 Technical Specifications

### Performance:
- **Frame Rate**: 60 FPS target
- **Audio Sampling**: 44.1kHz, 1024 sample chunks
- **Radar Refresh**: Real-time sweep updates
- **Target Capacity**: Dynamic with performance optimization

### Compatibility:
- **Python 3.7+** with standard scientific libraries
- **Cross-platform**: Windows, macOS, Linux
- **Audio Support**: Any microphone/line input
- **Graphics**: OpenGL-accelerated via Pygame

## 🚀 Use Cases

### Training & Education:
- Naval radar operator training
- Acoustic analysis education
- Target tracking practice
- Scenario-based learning

### Simulation & Analysis:
- Acoustic signal processing research
- Radar algorithm development
- Tactical scenario simulation
- Data analysis and visualization

### Development & Testing:
- UI/UX design for complex systems
- Real-time data visualization
- Audio processing algorithm testing
- Interactive system prototyping

## 📈 System Architecture

### Modular Design:
1. **Core Engine**: Main loop and event handling
2. **Audio Processing**: Real-time sound analysis
3. **Visualization**: 2D/3D rendering systems
4. **Data Management**: Recording and export systems
5. **UI Framework**: Interactive panel system
6. **Scenario Engine**: Mission scripting system

### Real-time Components:
- Continuous audio stream processing
- Dynamic target management
- Live radar sweep animation
- Instant UI feedback
- Real-time analytics updates

## 🎯 Learning Objectives

This project demonstrates:
- Real-time signal processing
- Interactive visualization techniques
- Complex state management
- Audio synthesis and playback
- Data logging and analysis
- User interface design for complex systems
- Scenario-based simulation
- Performance optimization for real-time applications

## 🔄 System Flow

1. **Audio Input** → Microphone capture
2. **Signal Processing** → FFT analysis and filtering
3. **Detection Logic** → Mode-specific target identification
4. **Visualization** → Radar display and UI updates
5. **Data Management** → Recording and export
6. **User Interaction** → Controls and feedback

## 📁 Project Structure

```
Advanced-Naval-Radar/
├── main.py                    # Main application
├── sessions/                  # Session recordings
├── screenshots/               # Screenshot captures
├── exports/                   # Data exports
├── recordings/                # Audio/video recordings
└── README.md                  # This documentation
```

## 🛠️ Technical Dependencies

### Required Libraries:
- **Pygame**: Graphics and audio framework
- **NumPy**: Numerical computing
- **SciPy**: Signal processing
- **SoundDevice**: Audio I/O
- **Matplotlib**: Data visualization (optional)
- **OpenCV**: Video export (optional)

### System Requirements:
- **Processor**: Multi-core for real-time processing
- **Memory**: 2GB+ for smooth operation
- **Audio**: Microphone or line input
- **Display**: 1280x720 minimum resolution
- **Storage**: 100MB+ for recordings

## 📚 Educational Value

This project serves as an excellent example of:
- Real-time system design
- Audio processing techniques
- Interactive visualization
- Complex state machines
- Data persistence strategies
- User interface development
- Simulation programming
- Performance optimization

## 🎉 Key Achievements

1. **Real-time Performance**: Smooth 60 FPS with complex calculations
2. **Modular Architecture**: Clean separation of concerns
3. **User Experience**: Intuitive controls and feedback
4. **Data Integrity**: Reliable logging and export systems
5. **Visual Fidelity**: Professional-grade radar display
6. **Audio Processing**: Sophisticated sound analysis
7. **Extensibility**: Easy to add new features and modes

## 🔮 Future Enhancements

Potential areas for expansion:
- Network multiplayer mode
- Advanced AI for target behavior
- Additional sensor types
- Historical playback mode
- Enhanced 3D visualization
- Mobile/tablet compatibility
- Cloud data synchronization
- Advanced analytics dashboard

## ⚠️ Notes & Limitations

- Requires microphone for full functionality
- Performance may vary with audio hardware
- Video export requires OpenCV installation
- 3D mode is experimental and basic
- Mission scenarios are pre-scripted
- No persistent database (file-based storage only)

---

*This project demonstrates advanced real-time system design, combining audio processing, visualization, and data management in an interactive naval radar simulation.*