from __future__ import print_function

import argparse
import logging
import os
import shlex
import shutil
import sys
import traceback
from typing import Optional

from PyInstaller.__main__ import run as run_pyinstaller

from . import __version__ as version
from . import config

# Import pro features
try:
    from .pro_features import build_cache, hidden_imports_detector
    from .security_features import code_obfuscator, antivirus_whitelist_generator
    PRO_FEATURES_AVAILABLE = True
    print("Pro features available in packaging module")
except ImportError as e:
    PRO_FEATURES_AVAILABLE = False
    print(f"Pro features not available in packaging: {e}")

logger = logging.getLogger(__name__)


def __get_pyinstaller_argument_parser():
    from PyInstaller.building.build_main import __add_options as add_build_options
    from PyInstaller.building.makespec import __add_options as add_makespec_options
    from PyInstaller.log import __add_options as add_log_options

    parser = argparse.ArgumentParser()

    add_makespec_options(parser)
    add_build_options(parser)
    add_log_options(parser)

    parser.add_argument(
        "filenames",
        metavar="scriptname",
        nargs="+",
        help=(
            "name of scriptfiles to be processed or "
            "exactly one .spec-file. If a .spec-file is "
            "specified, most options are unnecessary "
            "and are ignored."
        ),
    )  # From PyInstaller.__main__.run

    return parser


def get_pyinstaller_options():
    parser = __get_pyinstaller_argument_parser()

    options = []
    for action in parser._actions:
        # Clean out what we can't send over to the ui
        # Here is what we currently have: https://github.com/python/cpython/blob/master/Lib/argparse.py#L771
        del action.container
        options.append(action)

    return [o.__dict__ for o in options]


def will_packaging_overwrite_existing(file_path: str, manual_name: Optional[str], one_file: str, output_folder: str):
    """Checks if there is a possibility of a previous output being overwritten."""
    if not os.path.exists(output_folder):
        return False

    no_extension = manual_name if manual_name is not None else ".".join(os.path.basename(file_path).split(".")[:-1])
    if one_file and no_extension + ".exe" in os.listdir(output_folder):
        return True
    if (not one_file) and no_extension in os.listdir(output_folder):
        return True

    return False


def __move_package(src, dst):
    """Move the output package to the desired path (default is output/ - set in script.js)"""
    # Make sure the destination exists
    if not os.path.exists(dst):
        os.makedirs(dst)

    # Move all files/folders in dist/
    for file_or_folder in os.listdir(src):
        _dst = os.path.join(dst, file_or_folder)
        # If this already exists in the destination, delete it
        if os.path.exists(_dst):
            if os.path.isfile(_dst):
                os.remove(_dst)
            else:
                shutil.rmtree(_dst)
        # Move file
        shutil.move(os.path.join(src, file_or_folder), dst)


def package(pyinstaller_command, options):
    """
    Call PyInstaller to package a script using provided arguments and options.
    :param pyinstaller_command: Command to supply to PyInstaller
    :param options: auto-py-to-exe specific options for setup and cleaning up
    :return: Whether packaging was successful
    """

    # Show current version
    logger.info("Running auto-py-to-exe v" + version)

    # Extract script path from command for pro features
    script_path = _extract_script_path(pyinstaller_command)

    # Check for cached build first (Pro Feature)
    if PRO_FEATURES_AVAILABLE and config.PRO_FEATURES_ENABLED:
        cached_build = build_cache.get_cached_build(script_path, pyinstaller_command)
        if cached_build:
            logger.info("Using cached build - skipping PyInstaller execution")
            output_directory = os.path.abspath(options["outputDirectory"])
            try:
                __move_package(cached_build, output_directory)
                logger.info("Cached build moved to output directory successfully")
                return True
            except Exception as e:
                logger.warning(f"Failed to use cached build: {e}")
                # Continue with normal build process

    # Notify the user of the workspace and setup building to it
    logger.info("Building directory: {}".format(config.temporary_directory))

    # Pro Feature: Code Obfuscation
    original_script_path = script_path
    if PRO_FEATURES_AVAILABLE and config.OBFUSCATION_ENABLED and script_path:
        logger.info("Applying code obfuscation...")
        obfuscation_success, obfuscated_path, obfuscation_msg = code_obfuscator.obfuscate_script(
            script_path, config.temporary_directory
        )

        if obfuscation_success:
            logger.info(obfuscation_msg)
            # Update command to use obfuscated script
            pyinstaller_command = pyinstaller_command.replace(script_path, obfuscated_path)
            script_path = obfuscated_path
        else:
            logger.warning(f"Obfuscation failed: {obfuscation_msg}")

    # Pro Feature: Auto-detect hidden imports
    if PRO_FEATURES_AVAILABLE and config.HIDDEN_IMPORTS_AUTO_DETECT and script_path:
        logger.info("Auto-detecting hidden imports...")
        hidden_imports = hidden_imports_detector.detect_hidden_imports(original_script_path)

        if hidden_imports:
            # Add hidden imports to PyInstaller command
            hidden_imports_args = []
            for imp in hidden_imports:
                hidden_imports_args.extend(["--hidden-import", imp])

            # Insert hidden imports into the command
            pyinstaller_command += " " + " ".join(hidden_imports_args)
            logger.info(f"Added {len(hidden_imports)} hidden imports: {hidden_imports}")

    # Override arguments
    dist_path = os.path.join(config.temporary_directory, "application")
    build_path = os.path.join(config.temporary_directory, "build")
    extra_args = ["--distpath", dist_path] + ["--workpath", build_path] + ["--specpath", config.temporary_directory]

    logger.info("Provided command: {}".format(pyinstaller_command))

    # Setup options
    increase_recursion_limit = options["increaseRecursionLimit"]
    output_directory = os.path.abspath(options["outputDirectory"])

    if increase_recursion_limit:
        sys.setrecursionlimit(5000)
        logger.info("Recursion Limit is set to 5000")
    else:
        sys.setrecursionlimit(config.DEFAULT_RECURSION_LIMIT)

    # Run PyInstaller
    fail = False
    try:
        pyinstaller_args = shlex.split(pyinstaller_command) + extra_args

        # Display the command we are using and leave a space to separate out PyInstallers logs
        logger.info("Executing: {}".format(" ".join(pyinstaller_args)))
        logger.info("")

        run_pyinstaller(pyinstaller_args[1:])
    except:  # noqa: E722
        fail = True
        logger.exception("An error occurred while packaging")

    # Move project if there was no failure
    logger.info("")
    if not fail:
        logger.info("Moving project to: {0}".format(output_directory))
        try:
            __move_package(dist_path, output_directory)

            # Pro Feature: Cache successful build
            if PRO_FEATURES_AVAILABLE and config.PRO_FEATURES_ENABLED:
                build_cache.cache_build(original_script_path, pyinstaller_command, dist_path)

            # Pro Feature: Generate antivirus whitelist
            if PRO_FEATURES_AVAILABLE and config.ANTIVIRUS_WHITELIST_GENERATION:
                _generate_antivirus_whitelist(output_directory)

        except:  # noqa: E722
            logger.error("Failed to move project")
            logger.exception(traceback.format_exc())
    else:
        logger.info("Project output will not be moved to output folder")
        return False

    # Set complete
    return True


def _extract_script_path(pyinstaller_command: str) -> Optional[str]:
    """Extract the main script path from PyInstaller command"""
    try:
        args = shlex.split(pyinstaller_command)
        # Find the script file (usually the last argument without --)
        for i, arg in enumerate(args):
            if not arg.startswith('-') and arg.endswith('.py'):
                return arg
        return None
    except Exception:
        return None


def _generate_antivirus_whitelist(output_directory: str):
    """Generate antivirus whitelist for all executables in output directory"""
    try:
        for root, _, files in os.walk(output_directory):
            for file in files:
                if file.endswith('.exe'):
                    exe_path = os.path.join(root, file)
                    logger.info(f"Generating antivirus whitelist for: {exe_path}")
                    antivirus_whitelist_generator.generate_whitelist_info(exe_path)
    except Exception as e:
        logger.error(f"Failed to generate antivirus whitelist: {e}")
