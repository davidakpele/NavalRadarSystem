# Advanced Naval Acoustic Radar - Multi-Mode System v2.0

## Project Overview
A sophisticated naval acoustic radar simulation system designed for real-time target detection, classification, tracking, and tactical analysis. This system simulates various sonar/radar detection modes with realistic acoustic signature analysis and tactical decision support capabilities.

## Core Features

### 1. **Multi-Mode Detection System**
- **Passive Mode**: Stealth listening with wide coverage
- **Active Sonar**: Pulse echo ranging with high accuracy
- **Wide Beam**: Broad coverage with reduced range
- **Narrow Beam**: Focused sector scanning with enhanced accuracy
- **Omni-360**: Full 360-degree coverage with limited range

### 2. **Advanced Target Classification**
- **Acoustic Signature Analysis**: Analyzes frequency, modulation, harmonics, and source levels
- **Target Type Recognition**: Classifies contacts as:
  - Surface vessels (Merchant, Warship, Fast Attack Craft)
  - Subsurface contacts (Submarines, Torpedoes, UUVs)
  - Biological entities (Whales, Dolphins, Fish Schools)
  - Non-biological sources (Seismic surveys, Weather noise)
- **Threat Level Assignment**: Automatically categorizes targets as HOSTILE, UNKNOWN, NEUTRAL, or FRIENDLY

### 3. **Tactical Analysis Systems**

#### **Bearing Rate Tracker**
- Tracks bearing changes over time
- Predicts target crossing (ahead/astern)
- Calculates target aspect (bow, beam, quarter, stern)
- Detects rapid bearing changes indicating collision risk
- Visualizes bearing drift patterns

#### **SNR Analyzer**
- Calculates Signal-to-Noise Ratio for each target
- Provides detection confidence scores
- Assesses classification quality
- Monitors SNR trends (improving/degrading)
- Background noise level monitoring

#### **CPA (Closest Point of Approach) System**
- Calculates distance and time to closest approach
- Visualizes danger zones (2 NM radius)
- Predicts collision risks
- Color-coded threat assessment

### 4. **Torpedo Detection & Defense**
- **Automatic Detection**: Identifies high-speed underwater threats
- **Signature Analysis**: Recognizes torpedo acoustic profiles
- **Impact Prediction**: Calculates time to impact and intercept points
- **Countermeasure System**: 
  - Acoustic decoy deployment
  - Evasion recommendations
  - Real-time threat assessment
- **Alert System**: Visual and audio warnings for imminent threats

### 5. **Data Analytics & Visualization**
- **Trajectory Analysis**: Tracks target movement patterns
- **Heatmap Generation**: Visualizes target activity distribution
- **Collision Prediction**: Identifies potential target conflicts
- **Statistical Dashboard**: Real-time threat distribution and activity metrics

### 6. **Mission Scenario System**
- **Training Scenarios**: Pre-programmed mission profiles
- **Custom Scenario Creation**: User-defined target patterns and events
- **Progression Tracking**: Step-by-step mission objectives
- **Real-time Mission Control**: Start/stop and scenario cycling

### 7. **Recording & Data Management**
- **Session Recording**: Captures entire radar sessions
- **Multi-format Export**: CSV, JSON, and visual exports
- **Target History Logging**: Complete tracking data
- **Audio Recording**: Captures acoustic signatures
- **Screenshot Capability**: Instant radar screen captures

### 8. **3D Visualization Mode**
- **Perspective View**: 3D radar display with depth
- **Top-down View**: Traditional 2D radar display
- **Dynamic Camera Control**: Adjustable viewing angles
- **Depth Visualization**: Target distance representation

### 9. **Audio Processing System**
- **Real-time Audio Analysis**: Processes microphone input
- **Frequency Analysis**: FFT-based spectral analysis
- **Stereo Localization**: Determines sound direction
- **Noise Gating**: Background noise filtering
- **Gain Control**: Adjustable sensitivity

### 10. **Customizable Interface**
- **Multiple Color Themes**: Green, Blue, Amber, Red, Custom
- **Adjustable Brightness**: Screen brightness control
- **Grid & Compass Toggles**: Customizable display elements
- **CRT Effect**: Retro radar screen simulation
- **Zoom Control**: Adjustable radar range view

## Technical Capabilities

### Target Management
- Automatic target creation and tracking
- Velocity and angular velocity calculation
- Predicted position forecasting
- Trail visualization for movement history
- Target fading for stale contacts

### Acoustic Analysis
- Dominant frequency detection
- Modulation pattern recognition
- Harmonic content analysis
- Source level estimation
- Doppler shift calculation

### Real-time Processing
- 60 FPS radar display
- Real-time audio processing at 44.1kHz
- Concurrent target tracking (20+ targets)
- Dynamic threat assessment updates
- Immediate tactical recommendations

## User Interface Components

### Control Panels
1. **Detection Mode Selector**: Mode switching and configuration
2. **System Status Panel**: Real-time system metrics
3. **Own Ship Data**: Position, heading, speed, depth
4. **Tracked Targets**: Complete target list with tactical data
5. **Acoustic Sensor**: Live audio analysis display
6. **Recording Control**: Session management controls
7. **Analytics Dashboard**: Statistical overview
8. **Mission Control**: Scenario management
9. **Target Classification**: Detailed acoustic analysis
10. **Bearing Rate Tracker**: Crossing predictions
11. **SNR Analysis**: Signal quality metrics
12. **Torpedo Defense**: Threat assessment and countermeasures

### Visual Elements
- Radar circles with range markings (0-50 NM)
- Compass rose with cardinal directions
- Sweep lines with mode-specific effects
- Target icons with threat-based shapes
- Velocity vectors showing movement direction
- CPA visualization with danger zones
- Torpedo alerts with countdown timers

## Sound System
- **Target Detection Sounds**: Unique sounds per threat level
- **Sonar Pulses**: Active sonar ping effects
- **Echo Returns**: Realistic sonar echo simulation
- **Warning Alerts**: Critical threat notifications
- **UI Feedback**: Button clicks and mode changes
- **Ambient Sounds**: Optional background radar room noise
- **Volume Control**: Adjustable master volume

## Data Export Formats
- **CSV Export**: Tabular target data for spreadsheet analysis
- **JSON Export**: Structured data for programmatic processing
- **Session Recording**: Complete session playback capability
- **Heatmap Data**: Activity distribution matrices
- **Analytics Reports**: Statistical summaries and trends

## System Requirements & Architecture

### Dependencies
- PyGame for visualization and sound
- NumPy for numerical computations
- SciPy for signal processing
- SoundDevice for audio input
- Real-time processing capabilities

### Directory Structure
- `/recordings/`: Session recordings and audio captures
- `/sessions/`: JSON session data
- `/screenshots/`: Radar screen captures
- `/exports/`: CSV and JSON data exports

## Educational & Training Applications

### Naval Operations Training
- Sonar operator simulation
- Tactical decision-making practice
- Threat assessment exercises
- Emergency response training

### Acoustic Analysis Education
- Sound signature recognition
- Frequency analysis fundamentals
- Doppler effect visualization
- Signal processing concepts

### Maritime Safety
- Collision avoidance training
- CPA calculation practice
- Emergency maneuver simulation
- Multi-target tracking exercises

## Safety Features
- Automatic collision warnings
- CPA danger zone visualization
- Torpedo threat escalation
- Evasion recommendation system
- Critical alert prioritization

## Customization Options
- Adjustable detection thresholds
- Configurable audio filters
- Customizable display themes
- Variable radar ranges (5-100 NM)
- Adjustable zoom levels (0.5x-2.0x)

This system provides a comprehensive simulation environment for understanding naval acoustic radar operations, combining realistic physics, advanced signal processing, and tactical decision support in an interactive visual interface.