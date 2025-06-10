"""
Security Features Module for auto-py-to-exe
Provides code obfuscation and antivirus whitelist generation functionality.
"""

import hashlib
import json
import logging
import os
import platform
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import config

logger = logging.getLogger(__name__)


class CodeObfuscator:
    """Handles code obfuscation using various tools"""
    
    def __init__(self):
        self.supported_tools = {
            'pyarmor': self._obfuscate_with_pyarmor,
            'pyminifier': self._obfuscate_with_pyminifier,
            'python-minifier': self._obfuscate_with_python_minifier
        }
    
    def is_obfuscation_available(self) -> Tuple[bool, str]:
        """Check if obfuscation tools are available"""
        if not config.OBFUSCATION_ENABLED:
            return False, "Obfuscation is disabled in configuration"
        
        tool = config.OBFUSCATION_TOOL
        if tool not in self.supported_tools:
            return False, f"Unsupported obfuscation tool: {tool}"
        
        # Check if the tool is installed
        try:
            if tool == 'pyarmor':
                subprocess.run(['pyarmor', '--version'], capture_output=True, check=True)
            elif tool == 'pyminifier':
                subprocess.run(['pyminifier', '--version'], capture_output=True, check=True)
            elif tool == 'python-minifier':
                import python_minifier
            
            return True, f"Obfuscation tool '{tool}' is available"
            
        except (subprocess.CalledProcessError, ImportError, FileNotFoundError):
            return False, f"Obfuscation tool '{tool}' is not installed"
    
    def obfuscate_script(self, script_path: str, output_dir: str) -> Tuple[bool, str, str]:
        """
        Obfuscate a Python script
        Returns: (success, obfuscated_script_path, message)
        """
        available, message = self.is_obfuscation_available()
        if not available:
            return False, script_path, message
        
        try:
            tool = config.OBFUSCATION_TOOL
            obfuscated_path = self.supported_tools[tool](script_path, output_dir)
            
            if obfuscated_path and os.path.exists(obfuscated_path):
                logger.info(f"Script obfuscated successfully: {obfuscated_path}")
                return True, obfuscated_path, "Script obfuscated successfully"
            else:
                return False, script_path, "Obfuscation failed - no output generated"
                
        except Exception as e:
            logger.error(f"Obfuscation failed: {e}")
            return False, script_path, f"Obfuscation failed: {str(e)}"
    
    def _obfuscate_with_pyarmor(self, script_path: str, output_dir: str) -> Optional[str]:
        """Obfuscate using PyArmor"""
        try:
            # Create temporary directory for obfuscation
            temp_dir = tempfile.mkdtemp(prefix="pyarmor_")
            script_name = os.path.basename(script_path)
            obfuscated_name = f"obfuscated_{script_name}"
            
            # PyArmor command based on obfuscation level
            level_args = {
                'low': ['--restrict', '0'],
                'medium': ['--restrict', '1'],
                'high': ['--restrict', '4', '--advanced', '2']
            }
            
            args = level_args.get(config.OBFUSCATION_LEVEL, level_args['medium'])
            
            cmd = [
                'pyarmor', 'obfuscate',
                '--output', temp_dir,
                '--exact',
                *args,
                script_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Find the obfuscated file
            obfuscated_script = os.path.join(temp_dir, script_name)
            if os.path.exists(obfuscated_script):
                # Move to output directory
                final_path = os.path.join(output_dir, obfuscated_name)
                os.makedirs(output_dir, exist_ok=True)
                
                # Copy the obfuscated script and runtime files
                import shutil
                shutil.copy2(obfuscated_script, final_path)
                
                # Copy PyArmor runtime files if they exist
                runtime_dir = os.path.join(temp_dir, 'pytransform')
                if os.path.exists(runtime_dir):
                    shutil.copytree(runtime_dir, os.path.join(output_dir, 'pytransform'), dirs_exist_ok=True)
                
                return final_path
            
            return None
            
        except subprocess.CalledProcessError as e:
            logger.error(f"PyArmor obfuscation failed: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"PyArmor obfuscation error: {e}")
            return None
    
    def _obfuscate_with_pyminifier(self, script_path: str, output_dir: str) -> Optional[str]:
        """Obfuscate using pyminifier"""
        try:
            script_name = os.path.basename(script_path)
            obfuscated_name = f"obfuscated_{script_name}"
            output_path = os.path.join(output_dir, obfuscated_name)
            
            os.makedirs(output_dir, exist_ok=True)
            
            # Pyminifier options based on level
            level_args = {
                'low': ['--nominify'],
                'medium': ['--obfuscate'],
                'high': ['--obfuscate', '--gzip']
            }
            
            args = level_args.get(config.OBFUSCATION_LEVEL, level_args['medium'])
            
            cmd = [
                'pyminifier',
                *args,
                '--output', output_path,
                script_path
            ]
            
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            return output_path if os.path.exists(output_path) else None
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Pyminifier obfuscation failed: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Pyminifier obfuscation error: {e}")
            return None
    
    def _obfuscate_with_python_minifier(self, script_path: str, output_dir: str) -> Optional[str]:
        """Obfuscate using python-minifier"""
        try:
            import python_minifier
            
            script_name = os.path.basename(script_path)
            obfuscated_name = f"obfuscated_{script_name}"
            output_path = os.path.join(output_dir, obfuscated_name)
            
            os.makedirs(output_dir, exist_ok=True)
            
            with open(script_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # Minification options based on level
            if config.OBFUSCATION_LEVEL == 'low':
                minified = python_minifier.minify(source_code, remove_literal_statements=True)
            elif config.OBFUSCATION_LEVEL == 'medium':
                minified = python_minifier.minify(
                    source_code,
                    remove_literal_statements=True,
                    combine_imports=True,
                    hoist_literals=True
                )
            else:  # high
                minified = python_minifier.minify(
                    source_code,
                    remove_literal_statements=True,
                    combine_imports=True,
                    hoist_literals=True,
                    rename_locals=True,
                    rename_globals=True
                )
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(minified)
            
            return output_path
            
        except ImportError:
            logger.error("python-minifier not installed")
            return None
        except Exception as e:
            logger.error(f"python-minifier obfuscation error: {e}")
            return None


class AntivirusWhitelistGenerator:
    """Generates antivirus whitelist information for executables"""
    
    def __init__(self):
        self.whitelist_data = {}
    
    def generate_whitelist_info(self, executable_path: str) -> Dict:
        """Generate comprehensive whitelist information for an executable"""
        if not config.ANTIVIRUS_WHITELIST_GENERATION:
            return {}
        
        try:
            logger.info(f"Generating whitelist information for: {executable_path}")
            
            info = {
                'file_info': self._get_file_info(executable_path),
                'hashes': self._calculate_hashes(executable_path),
                'digital_signature': self._check_digital_signature(executable_path),
                'whitelist_instructions': self._generate_whitelist_instructions(),
                'common_av_exceptions': self._get_common_av_exceptions(executable_path),
                'generated_at': self._get_timestamp()
            }
            
            # Save whitelist info to file
            self._save_whitelist_file(executable_path, info)
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to generate whitelist info: {e}")
            return {}
    
    def _get_file_info(self, file_path: str) -> Dict:
        """Get basic file information"""
        try:
            stat = os.stat(file_path)
            return {
                'filename': os.path.basename(file_path),
                'full_path': os.path.abspath(file_path),
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created': self._format_timestamp(stat.st_ctime),
                'modified': self._format_timestamp(stat.st_mtime),
                'platform': platform.system(),
                'architecture': platform.architecture()[0]
            }
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            return {}
    
    def _calculate_hashes(self, file_path: str) -> Dict:
        """Calculate various hashes of the file"""
        hashes = {}
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Calculate multiple hash types
            hashes['md5'] = hashlib.md5(content).hexdigest()
            hashes['sha1'] = hashlib.sha1(content).hexdigest()
            hashes['sha256'] = hashlib.sha256(content).hexdigest()
            hashes['sha512'] = hashlib.sha512(content).hexdigest()
            
        except Exception as e:
            logger.error(f"Failed to calculate hashes: {e}")
        
        return hashes
    
    def _check_digital_signature(self, file_path: str) -> Dict:
        """Check if the file has a digital signature (Windows only)"""
        signature_info = {
            'is_signed': False,
            'signature_valid': False,
            'signer': None,
            'timestamp': None
        }
        
        if platform.system() == 'Windows':
            try:
                # Use PowerShell to check signature on Windows
                cmd = [
                    'powershell', '-Command',
                    f'Get-AuthenticodeSignature "{file_path}" | ConvertTo-Json'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    import json
                    sig_data = json.loads(result.stdout)
                    
                    signature_info['is_signed'] = sig_data.get('Status') == 'Valid'
                    signature_info['signature_valid'] = sig_data.get('Status') == 'Valid'
                    signature_info['signer'] = sig_data.get('SignerCertificate', {}).get('Subject')
                    
            except Exception as e:
                logger.warning(f"Could not check digital signature: {e}")
        
        return signature_info
    
    def _generate_whitelist_instructions(self) -> Dict:
        """Generate instructions for common antivirus software"""
        return {
            'windows_defender': {
                'method': 'Windows Security Settings',
                'steps': [
                    '1. Open Windows Security (Windows Defender)',
                    '2. Go to Virus & threat protection',
                    '3. Click on "Manage settings" under Virus & threat protection settings',
                    '4. Scroll down to Exclusions and click "Add or remove exclusions"',
                    '5. Click "Add an exclusion" and select "File"',
                    '6. Browse and select your executable file'
                ]
            },
            'avast': {
                'method': 'Avast Exclusions',
                'steps': [
                    '1. Open Avast Antivirus',
                    '2. Go to Settings > General > Exceptions',
                    '3. Click "Add Exception"',
                    '4. Select "File Path" and browse to your executable',
                    '5. Click "Add Exception"'
                ]
            },
            'norton': {
                'method': 'Norton Exclusions',
                'steps': [
                    '1. Open Norton Security',
                    '2. Click Settings',
                    '3. Click Antivirus',
                    '4. Click Scans and Risks',
                    '5. Click Exclusions/Low Risks',
                    '6. Click Configure next to Items to Exclude from Scans',
                    '7. Click Add and browse to your executable'
                ]
            },
            'mcafee': {
                'method': 'McAfee Exclusions',
                'steps': [
                    '1. Open McAfee Security Center',
                    '2. Click Virus and Spyware Protection',
                    '3. Click Real-Time Scanning',
                    '4. Click Excluded Files',
                    '5. Click Add File and browse to your executable'
                ]
            }
        }
    
    def _get_common_av_exceptions(self, file_path: str) -> List[str]:
        """Get list of common paths/patterns to exclude"""
        base_dir = os.path.dirname(os.path.abspath(file_path))
        filename = os.path.basename(file_path)
        
        return [
            file_path,  # Exact file path
            base_dir,   # Entire directory
            f"*{filename}",  # Filename pattern
            f"{base_dir}\\*",  # Directory pattern (Windows)
            f"{base_dir}/*",   # Directory pattern (Unix)
        ]
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _format_timestamp(self, timestamp: float) -> str:
        """Format timestamp to readable string"""
        from datetime import datetime
        return datetime.fromtimestamp(timestamp).isoformat()
    
    def _save_whitelist_file(self, executable_path: str, info: Dict):
        """Save whitelist information to a file"""
        try:
            base_name = os.path.splitext(executable_path)[0]
            whitelist_file = f"{base_name}_whitelist_info.json"
            
            with open(whitelist_file, 'w', encoding='utf-8') as f:
                json.dump(info, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Whitelist information saved to: {whitelist_file}")
            
        except Exception as e:
            logger.error(f"Failed to save whitelist file: {e}")


# Global instances
code_obfuscator = CodeObfuscator()
antivirus_whitelist_generator = AntivirusWhitelistGenerator()
