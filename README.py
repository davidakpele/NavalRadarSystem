# Naval Acoustic Radar System

## Project Overview

The Naval Acoustic Radar System is a real-time audio visualization application that transforms stereo microphone input into a military-grade radar display. The system detects sounds in your environment and displays them on a sweeping radar interface, calculating both the direction (bearing) and relative distance of audio sources.

## What It Does

This application creates an immersive sonar/radar experience by:

- **Listening** to your computer's stereo microphone input
- **Analyzing** the audio to determine direction using stereo channel differences
- **Visualizing** detected sounds as targets on a rotating radar display
- **Tracking** multiple sound sources simultaneously with persistent target identification
- **Displaying** comprehensive tactical information in military-style interface panels

## Core Functionality

### Real-Time Audio Analysis

The system continuously monitors stereo audio input and performs sophisticated signal processing:

- **Stereo Correlation Analysis**: Compares left and right audio channels to determine sound direction
- **Intensity Detection**: Measures the strength/loudness of incoming audio signals
- **Directional Calculation**: Uses time delay between stereo channels to calculate bearing angle
- **Noise Filtering**: Ignores low-level background noise (threshold: 0.01 intensity units)

### Target Detection and Tracking

When sound is detected above the threshold:

- **Automatic Target Creation**: New sound sources are assigned unique tracking IDs (T100, T101, T102, etc.)
- **Position Calculation**: Determines bearing (0-360°) and distance based on signal intensity
- **Target Persistence**: Tracks targets over time, even as they move or change
- **Target Merging**: Recognizes when multiple detections are the same source (within 15° tolerance)
- **Fade-Out System**: Gradually removes targets that are no longer detected
- **History Trails**: Maintains movement history for each target showing its path over time

## Visual Interface

### Main Radar Display

The central radar screen features:

- **Circular Radar Grid**: 320-pixel radius circular display with concentric range rings
- **Range Rings**: Four evenly-spaced circles representing distance intervals (5 NM per ring)
- **Radial Grid Lines**: 30° spacing for bearing reference
- **Rotating Sweep Line**: Continuously rotates at 2° per frame (full rotation every 3 seconds)
- **Sweep Trail Effect**: Fading green trail behind the sweep line (25 frames of decay)
- **Target Blips**: Bright green circular markers showing detected sound sources
- **Target IDs**: Labels on each blip showing unique identifier
- **Movement Trails**: Faint lines connecting historical positions of each target
- **Range Labels**: Distance markers on range rings (5NM, 10NM, 15NM, 20NM)

### Information Panels

The interface includes four comprehensive data panels on the right side:

#### 1. System Status Panel
Displays operational parameters:
- **Mode**: Radar orientation type (Head Up / North Up)
- **Range**: Current radar range setting (20 nautical miles)
- **Gain**: Audio sensitivity level with percentage (AUTO at 85%)
- **TX Status**: Transmission status indicator (TRANSMITTING)

#### 2. Own Ship Data Panel
Shows your vessel's position and movement:
- **HDG (Heading)**: Current compass direction (e.g., 342.5°)
- **SPD (Speed)**: Velocity in knots (e.g., 18.2 KTS)
- **LAT (Latitude)**: GPS latitude coordinates (e.g., 34° 02.1' N)
- **LON (Longitude)**: GPS longitude coordinates (e.g., 118° 24.9' W)

#### 3. Tracked Targets Panel
Comprehensive table of all detected contacts:
- **ID Column**: Unique target identifier (T100, T101, etc.)
- **RNG Column**: Range to target in nautical miles (e.g., 2.1NM)
- **BRG Column**: Bearing to target in degrees (e.g., 7°)
- **COG Column**: Course over ground - target's heading (e.g., 221°)
- **Capacity**: Displays up to 12 targets simultaneously
- **Sorting**: Targets sorted by range (closest first)

#### 4. Alerts Panel
Real-time warning system:
- **CPA Violation Monitoring**: Closest Point of Approach warnings
- **Proximity Alerts**: Warnings when targets come within 5 nautical miles
- **Alert Count**: Shows number of contacts violating safe distance
- **Status Display**: Shows "NONE" in green when all clear, or red warnings when threats detected

### Acoustic Sensor Indicator

A real-time audio monitoring display at the bottom left:
- **Signal Strength Bar**: Horizontal bar showing current audio intensity
- **Color Coding**: Green for normal levels, red for high intensity signals
- **Numeric Display**: Precise intensity value (0.00 to 1.00+)
- **Live Updates**: Refreshes every frame for immediate feedback

## Technical Specifications

### Display Parameters
- **Screen Resolution**: 1600 x 900 pixels
- **Radar Size**: 700 x 700 pixel area
- **Radar Radius**: 320 pixels
- **Frame Rate**: 60 frames per second
- **Color Scheme**: Military green on black background (phosphor CRT aesthetic)

### Audio Processing
- **Sampling Rate**: 44,100 Hz (CD quality)
- **Channels**: Stereo (2 channels - left and right)
- **Chunk Size**: 1024 samples per buffer
- **Detection Threshold**: 0.3 intensity units (adjustable)
- **Processing**: Real-time callback-based system

### Target Tracking
- **Maximum Targets**: 10 simultaneous tracked contacts
- **Target ID Range**: T100 to T109 (auto-increments)
- **History Length**: 20 historical positions per target
- **Fade Duration**: Approximately 85 frames (1.4 seconds at 60 FPS)
- **Direction Tolerance**: 15° for target association
- **Distance Calculation**: Linear scaling based on audio intensity

### Range and Bearing
- **Maximum Range**: 20 nautical miles (displayed)
- **Bearing System**: True bearing (0° = North, 90° = East, 180° = South, 270° = West)
- **Range Resolution**: Calculated from signal intensity (stronger = closer)
- **Angular Precision**: Sub-degree accuracy in direction finding

## Color Coding System

The application uses a military-inspired color scheme:

- **Primary Green (0, 255, 65)**: Active targets, sweep line, panel borders
- **Dark Green (0, 60, 20)**: Grid lines, range rings, inactive elements
- **Black (5, 8, 5)**: Background (slightly green-tinted for CRT effect)
- **Yellow (255, 255, 0)**: Panel titles and headers
- **Red (255, 50, 50)**: Warnings and alerts
- **Transparent Effects**: Alpha blending for trails and fading targets

## User Experience

### What You'll See

When you run the application:

1. **Initial Display**: Empty radar with rotating sweep line and grid
2. **Sound Detection**: When you make noise (clap, speak, play music), targets appear
3. **Directional Response**: Targets appear in the direction of the sound source
4. **Distance Indication**: Louder sounds appear closer to the center
5. **Persistence**: Targets fade slowly, creating a "memory" effect
6. **Panel Updates**: All information panels update in real-time

### How Sound Direction Works

The system determines direction using the **stereo time difference** principle:

- **Sound from Left**: Left microphone receives signal first → target appears on left side
- **Sound from Right**: Right microphone receives signal first → target appears on right side
- **Sound from Center**: Both microphones receive simultaneously → target appears straight ahead
- **Sound from Behind**: Complex correlation patterns → appears in rear sectors

### Distance Calculation

Distance is estimated from signal intensity:

- **Loud sounds**: Appear close to radar center (high intensity = close range)
- **Quiet sounds**: Appear farther from center (low intensity = distant)
- **Maximum range**: Very faint sounds appear at outer edge (20 NM display limit)

## Use Cases

### Entertainment
- Watch music visualize in real-time with directional awareness
- Create an immersive submarine/naval warfare atmosphere
- Gaming enhancement for naval or military-themed sessions

### Educational
- Demonstrate stereo audio principles and directionality
- Teach sonar/radar concepts in an interactive way
- Explore signal processing and spatial audio

### Practical
- Monitor acoustic environment with directional awareness
- Identify sound source locations in your space
- Audio debugging and microphone testing

## System Requirements

### Hardware
- **Computer**: Any modern PC or laptop
- **Microphone**: Stereo microphone or dual-channel audio input
- **Display**: Monitor supporting 1600x900 resolution or higher
- **Audio Interface**: Standard sound card with stereo input capability

### Software Dependencies
- **Python**: Version 3.7 or higher
- **Pygame**: Graphics and display rendering
- **NumPy**: Numerical processing and audio analysis
- **Sounddevice**: Real-time audio stream capture

### Performance
- **CPU Usage**: Moderate (continuous audio processing and rendering)
- **Memory**: Low (~50-100 MB typical)
- **Real-time Operation**: No lag or buffering in audio capture

## Limitations and Considerations

### Directional Accuracy
- **Stereo Limitation**: Can only determine left-right direction, not front-back
- **Microphone Spacing**: Works best with properly spaced stereo microphones
- **Acoustic Environment**: Reflections and echoes can affect accuracy
- **Single Plane**: Only detects horizontal direction, not elevation

### Distance Accuracy
- **Relative Only**: Distance is proportional to sound intensity, not actual physical distance
- **No Calibration**: System doesn't measure real-world distances
- **Volume Dependent**: A quiet nearby sound may appear farther than a loud distant sound
- **No Echo Ranging**: Unlike real sonar, doesn't use time-of-flight

### Target Tracking
- **No Persistence Between Sessions**: Targets are not saved when app closes
- **Limited Differentiation**: Cannot distinguish between different sound types
- **Overlap Issues**: Very close sound sources may merge into one target
- **Movement Tracking**: Shows history but doesn't predict future positions

## Future Enhancement Possibilities

Potential improvements that could be added:

- **Recording Capability**: Save radar sessions for playback and analysis
- **Sound Classification**: Identify types of sounds (voice, music, impacts)
- **True Distance Ranging**: Add echo-based distance measurement
- **3D Audio**: Incorporate elevation detection with multi-mic arrays
- **Network Sharing**: Multi-station radar network with data fusion
- **Target Export**: Save target tracks to CSV or other formats
- **Customizable Colors**: User-selectable color schemes and themes
- **Alert Configuration**: User-defined proximity warning thresholds
- **Zoom Controls**: Variable range settings (5NM, 10NM, 20NM, 50NM)

## Running the Application

### Basic Operation
1. Ensure microphone is connected and enabled
2. Run the Python script
3. Application window opens showing radar display
4. Make sounds to see targets appear
5. Close window or press system close button to exit

### Audio Source Tips
- **Test Sounds**: Clapping, snapping, speaking work well
- **Music**: Play stereo audio to see dynamic visualization
- **Movement**: Move around the microphone to see directional changes
- **Multiple Sources**: Have sounds from different locations simultaneously

### Troubleshooting
- **No Targets Appearing**: Check microphone permissions and volume levels
- **Wrong Direction**: Verify left/right channels aren't swapped
- **Constant Targets**: Reduce gain or move away from noise sources
- **Poor Performance**: Close other applications to free system resources

## Credits and Inspiration

This project draws inspiration from:
- **Naval Sonar Systems**: Military-grade acoustic detection technology
- **Air Traffic Control Radar**: Civilian radar display conventions
- **Submarine Warfare Games**: Entertainment applications of sonar visualization
- **Audio Engineering**: Professional sound localization techniques

## License and Usage

This is an educational and entertainment project demonstrating:
- Real-time audio processing concepts
- Stereo directionality principles
- Data visualization techniques
- User interface design for tactical displays

---

**Note**: This system is a simulation and visualization tool. It does not perform actual sonar ranging, cannot measure true distances, and is not suitable for navigation or safety-critical applications. It is designed purely for educational, entertainment, and demonstration purposes.