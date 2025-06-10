"""
Pro Features Module for auto-py-to-exe
Provides advanced functionality including build caching, obfuscation, and hidden imports detection.
"""

import hashlib
import json
import logging
import os
import pickle
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from . import config

logger = logging.getLogger(__name__)


class BuildCache:
    """Manages build caching for faster consecutive builds"""
    
    def __init__(self):
        self.cache_dir = Path(config.BUILD_CACHE_DIRECTORY)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self._load_metadata()
    
    def _load_metadata(self):
        """Load cache metadata"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.metadata = {}
        else:
            self.metadata = {}
    
    def _save_metadata(self):
        """Save cache metadata"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except IOError as e:
            logger.warning(f"Failed to save cache metadata: {e}")
    
    def _get_file_hash(self, file_path: str) -> str:
        """Calculate hash of a file"""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except IOError:
            return ""
    
    def _get_build_signature(self, script_path: str, pyinstaller_command: str) -> str:
        """Generate unique signature for a build configuration"""
        # Include script content hash, command, and modification time
        script_hash = self._get_file_hash(script_path)
        script_mtime = str(os.path.getmtime(script_path)) if os.path.exists(script_path) else "0"
        
        signature_data = f"{script_hash}:{script_mtime}:{pyinstaller_command}"
        return hashlib.sha256(signature_data.encode()).hexdigest()
    
    def get_cached_build(self, script_path: str, pyinstaller_command: str) -> Optional[str]:
        """Check if a cached build exists and is valid"""
        if not config.PRO_FEATURES_ENABLED:
            return None
            
        signature = self._get_build_signature(script_path, pyinstaller_command)
        
        if signature in self.metadata:
            cache_entry = self.metadata[signature]
            cache_path = self.cache_dir / cache_entry['cache_id']
            
            # Check if cache is still valid (not expired)
            cache_time = datetime.fromisoformat(cache_entry['timestamp'])
            if datetime.now() - cache_time < timedelta(days=config.BUILD_CACHE_RETENTION_DAYS):
                if cache_path.exists():
                    logger.info(f"Found valid cached build: {cache_path}")
                    return str(cache_path)
                else:
                    # Cache file missing, remove metadata entry
                    del self.metadata[signature]
                    self._save_metadata()
        
        return None
    
    def cache_build(self, script_path: str, pyinstaller_command: str, build_output_path: str) -> bool:
        """Cache a successful build"""
        if not config.PRO_FEATURES_ENABLED or not os.path.exists(build_output_path):
            return False
        
        try:
            signature = self._get_build_signature(script_path, pyinstaller_command)
            cache_id = f"build_{signature[:16]}_{int(time.time())}"
            cache_path = self.cache_dir / cache_id
            
            # Copy build output to cache
            if os.path.isdir(build_output_path):
                shutil.copytree(build_output_path, cache_path)
            else:
                shutil.copy2(build_output_path, cache_path)
            
            # Update metadata
            self.metadata[signature] = {
                'cache_id': cache_id,
                'timestamp': datetime.now().isoformat(),
                'script_path': script_path,
                'command': pyinstaller_command,
                'size_mb': self._get_directory_size(cache_path) / (1024 * 1024)
            }
            
            self._save_metadata()
            self._cleanup_old_cache()
            
            logger.info(f"Build cached successfully: {cache_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache build: {e}")
            return False
    
    def _get_directory_size(self, path: Path) -> int:
        """Calculate total size of directory in bytes"""
        total_size = 0
        try:
            if path.is_file():
                return path.stat().st_size
            for item in path.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
        except (OSError, IOError):
            pass
        return total_size
    
    def _cleanup_old_cache(self):
        """Remove old cache entries to maintain size limits"""
        try:
            # Calculate total cache size
            total_size_mb = sum(entry.get('size_mb', 0) for entry in self.metadata.values())
            
            if total_size_mb > config.BUILD_CACHE_MAX_SIZE_MB:
                # Sort by timestamp (oldest first)
                sorted_entries = sorted(
                    self.metadata.items(),
                    key=lambda x: x[1]['timestamp']
                )
                
                # Remove oldest entries until under limit
                for signature, entry in sorted_entries:
                    cache_path = self.cache_dir / entry['cache_id']
                    if cache_path.exists():
                        if cache_path.is_dir():
                            shutil.rmtree(cache_path)
                        else:
                            cache_path.unlink()
                    
                    del self.metadata[signature]
                    total_size_mb -= entry.get('size_mb', 0)
                    
                    if total_size_mb <= config.BUILD_CACHE_MAX_SIZE_MB * 0.8:  # 80% of limit
                        break
                
                self._save_metadata()
                logger.info("Cache cleanup completed")
                
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")
    
    def clear_cache(self):
        """Clear all cached builds"""
        try:
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.metadata = {}
            self._save_metadata()
            logger.info("Build cache cleared")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        total_entries = len(self.metadata)
        total_size_mb = sum(entry.get('size_mb', 0) for entry in self.metadata.values())
        
        return {
            'total_entries': total_entries,
            'total_size_mb': round(total_size_mb, 2),
            'cache_directory': str(self.cache_dir),
            'max_size_mb': config.BUILD_CACHE_MAX_SIZE_MB,
            'retention_days': config.BUILD_CACHE_RETENTION_DAYS
        }


class HiddenImportsDetector:
    """Automatically detects hidden imports for PyInstaller"""
    
    def __init__(self):
        self.detected_imports = set()
        self.scanned_files = set()
    
    def detect_hidden_imports(self, script_path: str) -> List[str]:
        """Detect hidden imports in a Python script"""
        if not config.HIDDEN_IMPORTS_AUTO_DETECT:
            return []
        
        logger.info(f"Scanning for hidden imports in: {script_path}")
        self.detected_imports.clear()
        self.scanned_files.clear()
        
        try:
            self._scan_file(script_path, depth=0)
            
            # Add common modules that are often missed
            self._add_common_hidden_imports()
            
            # Filter out standard library modules
            filtered_imports = self._filter_imports(list(self.detected_imports))
            
            logger.info(f"Detected {len(filtered_imports)} hidden imports: {filtered_imports}")
            return filtered_imports
            
        except Exception as e:
            logger.error(f"Failed to detect hidden imports: {e}")
            return []
    
    def _scan_file(self, file_path: str, depth: int):
        """Recursively scan a file for imports"""
        if depth > config.HIDDEN_IMPORTS_SCAN_DEPTH or file_path in self.scanned_files:
            return
        
        if not os.path.exists(file_path) or not file_path.endswith('.py'):
            return
        
        self.scanned_files.add(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Parse imports using AST for better accuracy
            import ast
            
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            self.detected_imports.add(alias.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            self.detected_imports.add(node.module.split('.')[0])
            except SyntaxError:
                # Fallback to regex parsing if AST fails
                self._scan_imports_regex(content)
            
            # Scan related files in the same directory
            base_dir = os.path.dirname(file_path)
            for item in os.listdir(base_dir):
                if item.endswith('.py') and item != os.path.basename(file_path):
                    self._scan_file(os.path.join(base_dir, item), depth + 1)
                    
        except Exception as e:
            logger.warning(f"Failed to scan file {file_path}: {e}")
    
    def _scan_imports_regex(self, content: str):
        """Fallback regex-based import scanning"""
        import re
        
        # Match import statements
        import_patterns = [
            r'^\s*import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
            r'^\s*from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s+import',
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                self.detected_imports.add(match.split('.')[0])
    
    def _add_common_hidden_imports(self):
        """Add commonly missed hidden imports"""
        for module in config.HIDDEN_IMPORTS_COMMON_MODULES:
            if any(imp.startswith(module) for imp in self.detected_imports):
                # Add related hidden imports for known problematic modules
                if module == "tkinter":
                    self.detected_imports.update(["tkinter.ttk", "tkinter.messagebox", "tkinter.filedialog"])
                elif module.startswith("PyQt"):
                    self.detected_imports.update([f"{module}.QtCore", f"{module}.QtGui", f"{module}.QtWidgets"])
                elif module == "matplotlib":
                    self.detected_imports.update(["matplotlib.backends", "matplotlib.backends.backend_tkagg"])
                elif module == "numpy":
                    self.detected_imports.update(["numpy.core", "numpy.lib"])
                elif module == "pandas":
                    self.detected_imports.update(["pandas.io", "pandas.plotting"])
    
    def _filter_imports(self, imports: List[str]) -> List[str]:
        """Filter out standard library and invalid imports"""
        import sys
        
        filtered = []
        stdlib_modules = set(sys.stdlib_module_names) if hasattr(sys, 'stdlib_module_names') else set()
        
        for imp in imports:
            # Skip standard library modules
            if imp in stdlib_modules:
                continue
            
            # Skip built-in modules
            if imp in sys.builtin_module_names:
                continue
            
            # Skip common false positives
            if imp in ['__future__', '__main__', 'typing']:
                continue
            
            # Try to import to verify it's a real module
            try:
                __import__(imp)
                filtered.append(imp)
            except ImportError:
                pass
        
        return sorted(list(set(filtered)))


# Global instances
build_cache = BuildCache()
hidden_imports_detector = HiddenImportsDetector()
