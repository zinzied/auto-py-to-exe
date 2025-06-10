import os
import sys


class UIOpenMode:
    NONE = 0
    CHROME_OR_EDGE = 1
    DEFAULT_BROWSER = 2


# Temporary directory for packaging scripts to speed up consecutive builds. Created on application start.
temporary_directory = None

# Frontend
FRONTEND_ASSET_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), "web")

# Pre-defined variables by Python
DEFAULT_RECURSION_LIMIT = sys.getrecursionlimit()

# Argument-influenced configuration
package_filename = None
ui_open_mode = UIOpenMode.CHROME_OR_EDGE
supplied_ui_configuration = None
default_output_directory = os.path.abspath("output")
language_hint = None

# Pro Features Configuration
PRO_FEATURES_ENABLED = True
BUILD_CACHE_DIRECTORY = os.path.join(os.path.expanduser("~"), ".auto-py-to-exe", "cache")
OBFUSCATION_ENABLED = False
HIDDEN_IMPORTS_AUTO_DETECT = True
ANTIVIRUS_WHITELIST_GENERATION = True

# Build cache settings
BUILD_CACHE_MAX_SIZE_MB = 1024  # 1GB default cache size
BUILD_CACHE_RETENTION_DAYS = 30  # Keep cache for 30 days

# Obfuscation settings
OBFUSCATION_TOOL = "pyarmor"  # Default obfuscation tool
OBFUSCATION_LEVEL = "medium"  # low, medium, high

# Hidden imports detection settings
HIDDEN_IMPORTS_SCAN_DEPTH = 3  # How deep to scan for imports
HIDDEN_IMPORTS_COMMON_MODULES = [
    "tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6", "kivy", "pygame",
    "numpy", "pandas", "matplotlib", "scipy", "sklearn", "tensorflow",
    "torch", "cv2", "PIL", "requests", "flask", "django", "fastapi"
]
