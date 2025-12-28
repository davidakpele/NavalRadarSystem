class ColorTheme:
    """Color theme definitions"""
    THEMES = {
        "green": {
            "primary": (0, 255, 65),
            "secondary": (0, 60, 20),
            "accent": (0, 255, 255),
            "warning": (255, 255, 0),
            "danger": (255, 50, 50),
            "bg": (5, 8, 5)
        },
        "blue": {
            "primary": (0, 191, 255),
            "secondary": (0, 20, 60),
            "accent": (173, 216, 230),
            "warning": (255, 215, 0),
            "danger": (255, 69, 0),
            "bg": (5, 5, 15)
        },
        "amber": {
            "primary": (255, 191, 0),
            "secondary": (60, 40, 0),
            "accent": (255, 215, 0),
            "warning": (255, 140, 0),
            "danger": (255, 0, 0),
            "bg": (15, 10, 0)
        },
        "red": {
            "primary": (255, 0, 0),
            "secondary": (60, 0, 0),
            "accent": (255, 100, 100),
            "warning": (255, 165, 0),
            "danger": (139, 0, 0),
            "bg": (15, 0, 0)
        },
        "custom": {
            "primary": (147, 112, 219),
            "secondary": (25, 25, 112),
            "accent": (186, 85, 211),
            "warning": (255, 215, 0),
            "danger": (220, 20, 60),
            "bg": (10, 10, 25)
        }
    }
    
    @staticmethod
    def get_theme(name):
        return ColorTheme.THEMES.get(name, ColorTheme.THEMES["green"])
