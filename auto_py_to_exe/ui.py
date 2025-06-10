import argparse
import json
import logging
import os

import eel
from eel import chrome, edge

from . import config, dialogs, packaging, utils

# Import pro features
try:
    from .pro_features import build_cache, hidden_imports_detector
    from .security_features import code_obfuscator, antivirus_whitelist_generator
    PRO_FEATURES_AVAILABLE = True
    print("Pro features loaded successfully")
except ImportError as e:
    print(f"Pro features not available: {e}")
    PRO_FEATURES_AVAILABLE = False

    # Dummy classes to prevent errors
    class DummyBuildCache:
        def get_cache_stats(self): return {}
        def clear_cache(self): pass

    class DummyCodeObfuscator:
        def is_obfuscation_available(self): return False, "Pro features not installed"

    class DummyHiddenImportsDetector:
        def detect_hidden_imports(self, script_path): return []

    # Create dummy instances
    build_cache = DummyBuildCache()
    code_obfuscator = DummyCodeObfuscator()
    hidden_imports_detector = DummyHiddenImportsDetector()

LOGGING_HANDLER_NAME = "auto-py-to-exe logging handler"

logger = logging.getLogger(__name__)


# Setup eels root folder
eel.init(config.FRONTEND_ASSET_FOLDER)


def __setup_logging_ui_forwarding():
    """Setup forwarding of logs by PyInstaller and auto-py-to-exe to the ui"""

    pyinstaller_logger = logging.getLogger("PyInstaller")
    # Make sure to check if the handler has already been setup so it doesn't get re-added on reload
    if not any([i.get_name() == LOGGING_HANDLER_NAME for i in pyinstaller_logger.handlers]):
        handler = logging.StreamHandler(utils.ForwardToFunctionStream(send_message_to_ui_output))
        handler.set_name(LOGGING_HANDLER_NAME)
        handler.setFormatter(logging.Formatter("%(relativeCreated)d %(levelname)s: %(message)s"))
        pyinstaller_logger.addHandler(handler)

    module_logger = logging.getLogger("auto_py_to_exe")
    if not any([i.get_name() == LOGGING_HANDLER_NAME for i in module_logger.handlers]):
        handler = logging.StreamHandler(utils.ForwardToFunctionStream(send_message_to_ui_output))
        handler.set_name(LOGGING_HANDLER_NAME)
        handler.setFormatter(logging.Formatter("%(message)s"))
        module_logger.addHandler(handler)


def __get_pyinstaller_options():
    options = packaging.get_pyinstaller_options()

    # Filter out removed arguments (PyInstaller v6.0.0 removed some arguments but added proper handlers for people still using them - we need to ignore them)
    options = [option for option in options if option["help"] != argparse.SUPPRESS]

    # In PyInstaller v6.0.0 --hide-console options were not set correctly (like --debug), fix them here
    for option in options:
        if isinstance(option["choices"], set):
            option["choices"] = list(option["choices"])

    return options


def __can_use_chrome():
    """Identify if Chrome is available for Eel to use"""
    chrome_instance_path = chrome.find_path()
    return chrome_instance_path is not None and os.path.exists(chrome_instance_path)


def __can_use_edge():
    """Identify if Edge is available for Eel to use"""
    return edge.find_path()


@eel.expose
def initialise():
    """Called by the UI when opened. Used to pass initial values and setup state we couldn't set until now."""
    __setup_logging_ui_forwarding()

    # Pass initial values to the client
    init_data = {
        "filename": config.package_filename,
        "suppliedUiConfiguration": config.supplied_ui_configuration,
        "options": __get_pyinstaller_options(),
        "warnings": utils.get_warnings(),
        "pathSeparator": os.pathsep,
        "defaultOutputFolder": config.default_output_directory,
        "languageHint": config.language_hint,
    }

    # Add pro features status
    if PRO_FEATURES_AVAILABLE:
        init_data["proFeatures"] = get_pro_features_status()
    else:
        init_data["proFeatures"] = {"available": False}

    return init_data


@eel.expose
def open_output_in_explorer(output_directory, input_filename, is_one_file):
    """Open a file in the local file explorer"""
    utils.open_output_in_explorer(output_directory, input_filename, is_one_file)


@eel.expose
def ask_file(file_type):
    """Ask the user to select a file"""
    return dialogs.ask_file(file_type)


@eel.expose
def ask_files():
    return dialogs.ask_files()


@eel.expose
def ask_folder():
    return dialogs.ask_folder()


@eel.expose
def does_file_exist(file_path):
    """Checks if a file exists"""
    return os.path.isfile(file_path)


@eel.expose
def does_folder_exist(path):
    """Checks if a folder exists"""
    return os.path.isdir(path)


@eel.expose
def is_file_an_ico(file_path):
    """Checks if a file is an ico file"""
    if not os.path.isfile(file_path):
        return None

    # Open the file and read the first 4 bytes
    with open(file_path, "rb") as f:
        data = f.read(4)
        if data == b"\x00\x00\x01\x00":
            return True
        else:
            return False


@eel.expose
def convert_path_to_absolute(path: str) -> str:
    """Converts a path to an absolute path if it exists. If it doesn't exist, returns the path as is."""
    if not os.path.exists(path):
        return path
    return os.path.abspath(path)


@eel.expose
def import_configuration():
    """Get configuration data from a file"""
    file_path = dialogs.ask_file("json")
    if file_path is not None:
        with open(file_path) as f:
            return json.load(f)
    else:
        return None


@eel.expose
def export_configuration(configuration):
    """Write configuration data to a file"""
    file_path = dialogs.ask_file_save_location("json")
    if file_path is not None:
        with open(file_path, "w") as f:
            json.dump(configuration, f, indent=True)


@eel.expose
def will_packaging_overwrite_existing(file_path, manual_name, one_file, output_folder):
    """Checks if there is a possibility of a previous output being overwritten"""
    return packaging.will_packaging_overwrite_existing(file_path, manual_name, one_file, output_folder)


@eel.expose
def package(command, non_pyinstaller_options):
    """Package the script provided using the options selected by the user"""
    packaging_options = {
        "increaseRecursionLimit": non_pyinstaller_options["increaseRecursionLimit"],
        "outputDirectory": non_pyinstaller_options["outputDirectory"],
    }

    packaging_successful = packaging.package(
        pyinstaller_command=command,
        options=packaging_options,
    )

    send_message_to_ui_output("Complete.\n")
    eel.signalPackagingComplete(packaging_successful)()


# Pro Features API Endpoints

@eel.expose
def get_pro_features_status():
    """Get the status of pro features"""
    if not PRO_FEATURES_AVAILABLE:
        return {
            'available': False,
            'message': 'Pro features not available'
        }

    return {
        'available': True,
        'enabled': config.PRO_FEATURES_ENABLED,
        'features': {
            'build_cache': config.PRO_FEATURES_ENABLED,
            'obfuscation': config.OBFUSCATION_ENABLED,
            'hidden_imports_detection': config.HIDDEN_IMPORTS_AUTO_DETECT,
            'antivirus_whitelist': config.ANTIVIRUS_WHITELIST_GENERATION
        },
        'obfuscation_tool': config.OBFUSCATION_TOOL,
        'obfuscation_level': config.OBFUSCATION_LEVEL
    }


@eel.expose
def get_build_cache_stats():
    """Get build cache statistics"""
    if not PRO_FEATURES_AVAILABLE:
        return {}

    try:
        return build_cache.get_cache_stats()
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {}


@eel.expose
def clear_build_cache():
    """Clear the build cache"""
    if not PRO_FEATURES_AVAILABLE:
        return False

    try:
        build_cache.clear_cache()
        send_message_to_ui_output("Build cache cleared successfully.\n")
        return True
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        send_message_to_ui_output(f"Failed to clear cache: {e}\n")
        return False


@eel.expose
def check_obfuscation_availability():
    """Check if code obfuscation is available"""
    if not PRO_FEATURES_AVAILABLE:
        return {'available': False, 'message': 'Pro features not available'}

    try:
        available, message = code_obfuscator.is_obfuscation_available()
        return {'available': available, 'message': message}
    except Exception as e:
        logger.error(f"Failed to check obfuscation: {e}")
        return {'available': False, 'message': f'Error: {e}'}


@eel.expose
def detect_hidden_imports(script_path):
    """Detect hidden imports for a script"""
    if not PRO_FEATURES_AVAILABLE or not script_path:
        return []

    try:
        imports = hidden_imports_detector.detect_hidden_imports(script_path)
        send_message_to_ui_output(f"Detected {len(imports)} hidden imports.\n")
        return imports
    except Exception as e:
        logger.error(f"Failed to detect hidden imports: {e}")
        send_message_to_ui_output(f"Failed to detect hidden imports: {e}\n")
        return []


@eel.expose
def update_pro_feature_setting(feature, enabled):
    """Update a pro feature setting"""
    if not PRO_FEATURES_AVAILABLE:
        return False

    try:
        if feature == 'build_cache':
            config.PRO_FEATURES_ENABLED = enabled
        elif feature == 'obfuscation':
            config.OBFUSCATION_ENABLED = enabled
        elif feature == 'hidden_imports_detection':
            config.HIDDEN_IMPORTS_AUTO_DETECT = enabled
        elif feature == 'antivirus_whitelist':
            config.ANTIVIRUS_WHITELIST_GENERATION = enabled
        else:
            return False

        send_message_to_ui_output(f"Pro feature '{feature}' {'enabled' if enabled else 'disabled'}.\n")
        return True
    except Exception as e:
        logger.error(f"Failed to update setting: {e}")
        return False


@eel.expose
def update_obfuscation_settings(tool, level):
    """Update obfuscation settings"""
    if not PRO_FEATURES_AVAILABLE:
        return False

    try:
        config.OBFUSCATION_TOOL = tool
        config.OBFUSCATION_LEVEL = level
        send_message_to_ui_output(f"Obfuscation settings updated: {tool} ({level}).\n")
        return True
    except Exception as e:
        logger.error(f"Failed to update obfuscation settings: {e}")
        return False


def send_message_to_ui_output(message):
    """Show a message in the ui output"""
    eel.putMessageInOutput(message)()


def start(open_mode):
    """Start the UI using Eel"""
    try:
        chrome_available = __can_use_chrome()
        edge_available = __can_use_edge()

        if open_mode == config.UIOpenMode.CHROME_OR_EDGE and chrome_available:
            print("The interface is being opened in a new Chrome window")
            print(
                "Please do not close this terminal while using auto-py-to-exe - the process will end when the window is closed"
            )
            eel.start("index.html", size=(650, 672), port=0, mode="chrome")
        elif open_mode == config.UIOpenMode.CHROME_OR_EDGE and edge_available:
            print("The interface is being opened in a new Edge window")
            print(
                "Please do not close this terminal while using auto-py-to-exe - the process will end when the window is closed"
            )
            eel.start("index.html", size=(650, 673), port=0, mode="edge")
        elif open_mode == config.UIOpenMode.DEFAULT_BROWSER or (
            open_mode == config.UIOpenMode.CHROME_OR_EDGE and not chrome_available and not edge_available
        ):
            print("The interface is being opened in your default browser")
            print(
                "Please do not close this terminal while using auto-py-to-exe - the process will end when the window is closed"
            )
            eel.start("index.html", size=(650, 672), port=0, mode="user default")
        else:
            port = utils.get_port()
            print(f"Server starting at http://localhost:{port}/index.html")
            print("You may end this process using Ctrl+C when finished using auto-py-to-exe")
            eel.start("index.html", host="localhost", port=port, mode=None, close_callback=lambda x, y: None)
    except (SystemExit, KeyboardInterrupt):
        pass  # This is what the bottle server raises
