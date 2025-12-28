def print_help():
    """Print keyboard shortcuts help"""
    help_text = """
    ╔══════════════════════════════════════════════════════════════╗
    ║           ADVANCED NAVAL RADAR - KEYBOARD SHORTCUTS          ║
    ╠══════════════════════════════════════════════════════════════╣
    ║ DETECTION MODES:                                             ║
    ║   1-5      : Switch detection modes                          ║
    ║   SPACE    : Sonar pulse (Active mode) / Pause               ║
    ║   ←/→      : Adjust narrow beam angle                        ║
    ║                                                              ║
    ║ 3D VISUALIZATION:                                            ║
    ║   B        : Toggle 3D visualization mode                    ║
    ║                                                              ║
    ║ MISSION SYSTEM:                                              ║
    ║   M        : Start/Stop mission scenario                     ║
    ║   N        : Cycle through scenarios                         ║
    ║                                                              ║
    ║ ANALYTICS:                                                   ║
    ║   A        : Export analytics data                           ║
    ║                                                              ║
    ║ SOUND CONTROLS:                                              ║
    ║   V        : Toggle mute/unmute                              ║
    ║   ↑/↓      : Volume up/down                                  ║
    ║   L        : Toggle detection sounds                         ║
    ║   K        : Toggle sweep sounds                             ║
    ║                                                              ║
    ║ RECORDING:                                                   ║
    ║   R        : Start/Stop recording                            ║
    ║   S        : Take screenshot                                 ║
    ║   E        : Export targets to CSV                           ║
    ║   J        : Export targets to JSON                          ║
    ║   C        : Clear all targets                               ║
    ║                                                              ║
    ║ DISPLAY:                                                     ║
    ║   T        : Cycle color themes                              ║
    ║   B/D      : Brightness up/down                              ║
    ║   G        : Toggle grid                                     ║
    ║   O        : Toggle compass                                  ║
    ║   X        : Toggle CRT effect                               ║
    ║   +/-      : Zoom in/out                                     ║
    ║   0        : Reset zoom                                      ║
    ║   [/]      : Decrease/Increase range                         ║
    ║                                                              ║
    ║ AUDIO:                                                       ║
    ║   ,/.      : Gain control down/up                            ║
    ║   F        : Cycle frequency filters                         ║
    ║   N/M      : Noise gate up/down                              ║
    ║   Y/U      : Target size filter down/up                      ║
    ║                                                              ║
    ║ OTHER:                                                       ║
    ║   H        : Show this help                                  ║
    ║   ESC      : Exit                                            ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(help_text)