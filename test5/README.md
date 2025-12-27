# Multi-Mode Detection System - Complete Guide

## 🎯 Overview

This advanced radar system features **5 different detection modes**, each optimized for different tactical scenarios. Switch between modes instantly with keyboard shortcuts and see real-time updates in comprehensive UI panels.

---

## 🔄 Detection Modes

### 1. 🟢 **PASSIVE MODE** (Key: 1)

**Description:** Stealth listening mode

**Characteristics:**
- **Detection Arc:** 60° (narrow)
- **Range:** Standard (20 NM)
- **Accuracy:** 70%
- **Sweep Speed:** Normal (3°/frame)
- **Color:** Green
- **Stealth:** High (no emissions)

**Best For:**
- Stealth operations
- Covert surveillance
- Avoiding detection
- Standard operations

**How It Works:**
- Listens passively to ambient sounds
- No active transmissions
- Detects targets as sweep passes over them
- 60° detection cone around sweep line

**Visual:**
```
     60° arc
      / \
     /   \
    /  ●  \ ← Sweep line
   /       \
  /_________\
```

---

### 2. 🔵 **ACTIVE SONAR MODE** (Key: 2)

**Description:** Pulse echo ranging for true distance

**Characteristics:**
- **Detection Arc:** 45° (focused)
- **Range:** Extended (40 NM)
- **Accuracy:** 95% (highest)
- **Sweep Speed:** Slow (2°/frame)
- **Color:** Cyan
- **Shows True Distance:** YES

**Best For:**
- Accurate ranging
- Target identification
- Combat situations
- Clear tactical picture

**How It Works:**
1. Press **SPACE** to send sonar pulse
2. Expanding cyan ring shows pulse propagation
3. Echoes return from targets
4. Distance calculated from echo delay
5. More accurate than passive intensity estimation

**Visual:**
```
Send pulse: ●───○───○───○ (expanding rings)
            ↓   ↓   ↓   ↓
Echoes:     ●←──────────● (return from target)
```

**Controls:**
- **SPACE:** Send sonar pulse (every 2+ seconds)
- Pulse visible for 2 seconds
- Automatic echo detection

**Note:** Active sonar reveals your position to others!

---

### 3. 🟡 **WIDE BEAM MODE** (Key: 3)

**Description:** Broad coverage, lower accuracy

**Characteristics:**
- **Detection Arc:** 120° (very wide)
- **Range:** Reduced (14 NM)
- **Accuracy:** 40%
- **Sweep Speed:** Fast (4°/frame)
- **Color:** Yellow
- **Trade-off:** Coverage over precision

**Best For:**
- Quick area scans
- Multiple target scenarios
- Situational awareness
- Threat assessment

**How It Works:**
- 120° wide beam covers large area per sweep
- Faster rotation for quick full-circle scan
- Lower accuracy due to wide beam spread
- More targets detected simultaneously

**Visual:**
```
    120° wide arc
   ____________
  /            \
 |      ●       | ← Wide beam
  \____________/
```

**Detection Pattern:**
- Detects anything within 120° arc of sweep
- Full 360° scan in ~90 frames (1.5 seconds)
- Good for busy environments

---

### 4. 🟠 **NARROW BEAM MODE** (Key: 4)

**Description:** Focused sector with high precision

**Characteristics:**
- **Detection Arc:** 30° (very narrow)
- **Range:** Good (30 NM)
- **Accuracy:** 90%
- **Sweep Speed:** Very slow (1°/frame) - but FIXED
- **Color:** Orange
- **User Controlled:** YES

**Best For:**
- Tracking specific targets
- Investigating specific direction
- High-precision detection
- Focused monitoring

**How It Works:**
- Beam stays pointed in fixed direction
- Use **LEFT/RIGHT arrow keys** to rotate beam
- Only detects in 30° cone ahead of beam
- Very accurate within cone

**Visual:**
```
   30° focused
      /\
     /  \
    | ●  | ← User-controlled
     \  /   beam direction
      \/
```

**Controls:**
- **← LEFT arrow:** Rotate beam left (-5° per press)
- **→ RIGHT arrow:** Rotate beam right (+5° per press)
- Yellow lines show beam edges

**Strategy:**
- Point at suspected target location
- Hold on area of interest
- High accuracy for investigation

---

### 5. 🔵 **360° OMNI MODE** (Key: 5)

**Description:** All directions simultaneously

**Characteristics:**
- **Detection Arc:** 360° (complete coverage)
- **Range:** Short (10 NM)
- **Accuracy:** 30% (lowest)
- **Sweep Speed:** None (no sweep)
- **Color:** Blue
- **Instant Coverage:** YES

**Best For:**
- Maximum awareness
- Defensive posture
- Crowded environments
- Emergency situations

**How It Works:**
- Detects in all directions at once
- No sweep line (pulsing circle instead)
- Simultaneous multi-directional sensing
- Sacrifices range and accuracy for coverage

**Visual:**
```
      ●   ●
    ●   ○   ● ← All directions
      ●   ●    at once
   (pulsing circle)
```

**Display:**
- Blue pulsing circle instead of sweep
- Targets appear from any direction
- No waiting for sweep to pass

---

## 🎮 Controls Reference

### Mode Selection
| Key | Mode | Color |
|-----|------|-------|
| **1** | PASSIVE | 🟢 Green |
| **2** | ACTIVE SONAR | 🔵 Cyan |
| **3** | WIDE BEAM | 🟡 Yellow |
| **4** | NARROW BEAM | 🟠 Orange |
| **5** | 360° OMNI | 🔵 Blue |

### Mode-Specific Controls
| Key | Action | Mode |
|-----|--------|------|
| **SPACE** | Send sonar pulse | Active Sonar |
| **← LEFT** | Rotate beam left | Narrow Beam |
| **→ RIGHT** | Rotate beam right | Narrow Beam |

### General Controls
| Key | Action |
|-----|--------|
| **ESC** | Exit application |
| **E** | Export selected target |
| **A** | Export all targets |
| **Mouse Click** | Select/lock target |

---

## 📊 UI Panels (5 Panels)

### 1. **DETECTION MODE Panel** (Top-Left)

Shows all available modes with current selection:

```
DETECTION MODE
━━━━━━━━━━━━━━━━
■ 1: PASSIVE        ← Selected (filled square)
□ 2: ACTIVE SONAR   ← Available (empty square)
□ 3: WIDE BEAM
□ 4: NARROW BEAM
□ 5: 360° OMNI
━━━━━━━━━━━━━━━━
SPACE: Send sonar pulse
←→: Adjust narrow beam
```

**Features:**
- Current mode highlighted with filled square
- Mode color-coded
- Shortcut keys displayed
- Quick mode descriptions

---

### 2. **SYSTEM STATUS Panel** (Left, Second)

Displays current operational parameters:

```
SYSTEM STATUS
━━━━━━━━━━━━━━━━
MODE:       PASSIVE
RANGE:      20 NM
ACCURACY:   70%
GAIN:       AUTO (85%)
TX STATUS:  TRANSMITTING
```

**Updates Dynamically:**
- Range changes with mode
- Accuracy reflects current mode
- TX status shows transmission state

---

### 3. **OWN SHIP DATA Panel** (Left, Third)

Shows your vessel information:

```
OWN SHIP DATA
━━━━━━━━━━━━━━━━
HDG:        342.5°
SPD:        18.2 KTS
LAT:        34° 02.1' N
LON:        118° 24.9' W
DEPTH:      150 M
```

**Live Updates:**
- Heading drifts slightly (realistic)
- Speed fluctuates
- Position data displayed
- Depth shown

---

### 4. **TRACKED TARGETS Panel** (Left, Fourth)

Lists all detected targets in table format:

```
TRACKED TARGETS
━━━━━━━━━━━━━━━━━━━━━━
ID   RNG    BRG   VEL   THR
━━━━━━━━━━━━━━━━━━━━━━
T1   2.1    7°    45    FRI
T2   5.3    264°  23    NEU
T3   11.2   198°  67    THR
...
```

**Columns:**
- **ID:** Target identifier
- **RNG:** Range in nautical miles
- **BRG:** Bearing in degrees (0-360°)
- **VEL:** Velocity in px/s
- **THR:** Threat level (FRI/NEU/THR)

**Features:**
- Sorted by range (closest first)
- Color-coded by threat
- Shows up to 15 targets
- Real-time updates

---

### 5. **ACOUSTIC SENSOR Panel** (Top-Right)

Real-time audio sensor display:

```
ACOUSTIC SENSOR
━━━━━━━━━━━━━━━━━━━
███████████░░░░░░░░  0.65
━━━━━━━━━━━━━━━━━━━
FREQ:      440 Hz
BEARING:   45.3°
```

**Components:**
- **Signal bar:** Visual intensity meter
- **Intensity value:** 0.00 to 1.00+
- **Frequency:** Dominant frequency
- **Bearing:** Sound direction

**Color Coding:**
- Green bar: Normal (<0.7)
- Red bar: High (≥0.7)

---

## 🎯 Mode Comparison Table

| Feature | Passive | Active Sonar | Wide Beam | Narrow Beam | 360° Omni |
|---------|---------|--------------|-----------|-------------|-----------|
| **Range** | 20 NM | 40 NM | 14 NM | 30 NM | 10 NM |
| **Accuracy** | 70% | 95% | 40% | 90% | 30% |
| **Coverage** | 60° | 45° | 120° | 30° | 360° |
| **Stealth** | High | Low | Medium | Medium | Low |
| **Speed** | Normal | Slow | Fast | Fixed | Instant |
| **True Distance** | No | Yes | No | No | No |
| **Best For** | General | Combat | Scanning | Focus | Defense |

---

## 💡 Tactical Usage Guide

### Mission Scenarios

#### **Scenario 1: Covert Surveillance**
**Use:** PASSIVE MODE (Key 1)
- Maintain stealth
- Monitor area quietly
- Avoid detection
- Standard patrol

#### **Scenario 2: Target Identification**
**Use:** ACTIVE SONAR MODE (Key 2)
- Get exact range to target
- Verify target position
- Combat engagement
- Press SPACE to ping
- Accept detection risk for accuracy

#### **Scenario 3: Quick Area Scan**
**Use:** WIDE BEAM MODE (Key 3)
- Fast 360° coverage
- Multiple targets
- Threat assessment
- Initial reconnaissance

#### **Scenario 4: Tracking Specific Target**
**Use:** NARROW BEAM MODE (Key 4)
- Point at target
- Use ←→ to adjust
- High precision tracking
- Investigation

#### **Scenario 5: Under Attack**
**Use:** 360° OMNI MODE (Key 5)
- See all threats instantly
- Defensive awareness
- No blind spots
- Emergency response

---

## 🔬 Technical Details

### Detection Logic by Mode

**PASSIVE:**
```
if (angle_difference < 15°) {
    detect_target();
}
```

**ACTIVE SONAR:**
```
send_pulse();
wait_for_echo();
calculate_distance_from_echo_time();
detect_with_high_accuracy();
```

**WIDE BEAM:**
```
if (angle_difference < 60°) {
    detect_target();
}
```

**NARROW BEAM:**
```
if (angle_difference_from_beam < 15°) {
    detect_with_high_precision();
}
```

**360° OMNI:**
```
detect_all_directions_simultaneously();
```

---

## 🎨 Visual Indicators

### Mode Colors
- 🟢 **Green:** Passive (stealth)
- 🔵 **Cyan:** Active Sonar (ranging)
- 🟡 **Yellow:** Wide Beam (coverage)
- 🟠 **Orange:** Narrow Beam (focus)
- 🔵 **Blue:** 360° Omni (all-around)

### Sweep Line Styles
- **Passive/Active/Wide:** Rotating sweep with trail
- **Narrow:** Fixed beam at user angle
- **360° Omni:** Pulsing circle (no sweep)

### Special Effects
- **Active Sonar:** Expanding cyan rings on pulse
- **Narrow Beam:** Beam edge lines shown
- **Wide Beam:** Wide arc indicators
- **360° Omni:** Breathing circle effect

---

## 📈 Performance Impact

| Mode | CPU Usage | Detection Rate | Frame Rate |
|------|-----------|----------------|------------|
| Passive | Low | Normal | 60 FPS |
| Active Sonar | Medium | Burst | 60 FPS |
| Wide Beam | Medium | High | 60 FPS |
| Narrow Beam | Low | Low | 60 FPS |
| 360° Omni | High | Very High | 55-60 FPS |

**Notes:**
- 360° Omni uses most CPU (checking all angles)
- Active Sonar pulse calculations add overhead
- All modes maintain good frame rate

---

## 🔧 Configuration Values

Each mode can be customized in code:

```python
"PASSIVE": {
    "detection_arc": 60,      # degrees
    "range_multiplier": 1.0,  # 1x base range
    "accuracy": 0.7,          # 70%
    "sweep_speed": 3          # degrees per frame
}
```

Change these to adjust mode characteristics!

---

## 💡 Pro Tips

### 1. **Mode Switching Strategy**
- Start with PASSIVE for general patrol
- Switch to WIDE BEAM when contacts suspected
- Use NARROW BEAM to investigate specific contact
- Activate ACTIVE SONAR for combat engagement
- Emergency? Hit 360° OMNI

### 2. **Active Sonar Timing**
- Don't spam SPACE (2-second minimum between pulses)
- Pulse when you need exact range
- Accept that enemies will know your location
- Use sparingly in stealth missions

### 3. **Narrow Beam Technique**
- Point at area of interest before switching
- Use ←→ to sweep slowly
- Good for tracking single target
- Combine with Active Sonar for best results

### 4. **Coverage vs Accuracy**
```
High Coverage → Low Accuracy:
360° OMNI > WIDE BEAM > PASSIVE > NARROW BEAM > ACTIVE SONAR

High Accuracy → Low Coverage:
ACTIVE SONAR > NARROW BEAM > PASSIVE > WIDE BEAM > 360° OMNI
```

### 5. **Range Management**
- Long range needed? Use ACTIVE SONAR
- Close quarters? 360° OMNI works great
- Match mode to expected target distance

---

## 🐛 Troubleshooting

### Issue: Mode won't switch
**Solution:** Make sure you're not holding keys. Press once cleanly.

### Issue: No sonar pulse visible
**Solution:** You must be in ACTIVE SONAR mode (key 2) first, then press SPACE.

### Issue: Narrow beam not moving
**Solution:** Use arrow keys (← →), not mouse. Each press rotates 5°.

### Issue: Too many false contacts in OMNI
**Solution:** Normal behavior - OMNI has lowest accuracy (30%). Use PASSIVE for cleaner results.

### Issue: Can't see targets in NARROW BEAM
**Solution:** Targets only appear within the 30° beam. Rotate with ← → to find them.

---

## 🎓 Training Exercise

### Complete Mode Familiarization:

1. **Start in PASSIVE** (Key 1)
   - Make noise, watch targets appear on sweep

2. **Switch to WIDE BEAM** (Key 3)
   - Notice faster sweep, wider coverage

3. **Try NARROW BEAM** (Key 4)
   - Use ← → to aim at a target
   - See higher accuracy

4. **Activate ACTIVE SONAR** (Key 2)
   - Press SPACE to send pulse
   - Watch cyan rings expand
   - See accurate distance

5. **Emergency Mode** (Key 5)
   - Switch to 360° OMNI
   - See instant all-around detection

6. **Compare Results**
   - Note differences in detection
   - Understand trade-offs
   - Choose best mode for situation

---

**Master all 5 modes to become a complete radar operator!**