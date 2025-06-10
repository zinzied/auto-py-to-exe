# 🚀 Auto-py-to-exe Pro Features

This document describes the advanced pro features available in auto-py-to-exe that enhance the build process with professional-grade capabilities.

## 📋 Overview

The pro features add powerful functionality to auto-py-to-exe:

- ⚡ **Build Caching** - Dramatically faster consecutive builds
- 🔍 **Hidden Imports Auto-Detection** - Automatic dependency discovery
- 🔒 **Code Obfuscation** - Protect your source code
- 🛡️ **Antivirus Whitelist Generation** - Reduce false positives

## 🛠️ Installation

### Quick Install
Run the installation script from the auto-py-to-exe root directory:

```bash
python install_pro_features.py
```

### Manual Installation
Install the optional dependencies manually:

```bash
# For code obfuscation
pip install pyarmor
pip install pyminifier  
pip install python-minifier
```

## 🚀 Features

### ⚡ Build Caching

**What it does:** Caches successful builds to dramatically speed up consecutive builds with the same configuration.

**Benefits:**
- 🚀 Up to 90% faster rebuild times
- 💾 Intelligent cache management with size limits
- 🧹 Automatic cleanup of old cache entries
- 📊 Cache statistics and monitoring

**Configuration:**
- Cache directory: `~/.auto-py-to-exe/cache`
- Default cache size limit: 1GB
- Default retention: 30 days

**Usage:**
1. Enable "Build Caching" in the Pro Features section
2. Build your project normally
3. Subsequent builds with the same configuration will use cached results

### 🔍 Hidden Imports Auto-Detection

**What it does:** Automatically scans your Python code to detect hidden imports that PyInstaller might miss.

**Benefits:**
- 🔍 Finds imports that PyInstaller's analysis misses
- 📦 Reduces "module not found" errors in built executables
- 🎯 Supports popular libraries (tkinter, PyQt, numpy, etc.)
- ⚡ Configurable scan depth and patterns

**Supported Libraries:**
- GUI frameworks: tkinter, PyQt5/6, PySide2/6, kivy
- Data science: numpy, pandas, matplotlib, scipy, sklearn
- Web frameworks: flask, django, fastapi
- And many more...

**Usage:**
1. Enable "Auto-detect Hidden Imports"
2. Click "Scan Current Script" to preview detected imports
3. Hidden imports are automatically added during build

### 🔒 Code Obfuscation

**What it does:** Obfuscates your Python source code before packaging to protect intellectual property.

**Supported Tools:**
- **PyArmor** - Professional-grade obfuscation with runtime protection
- **Pyminifier** - Code minification and obfuscation
- **Python-minifier** - Lightweight code minification

**Obfuscation Levels:**
- **Low** - Basic minification, preserves readability
- **Medium** - Moderate obfuscation, good balance
- **High** - Maximum obfuscation, best protection

**Usage:**
1. Install obfuscation tools (done automatically by installer)
2. Enable "Code Obfuscation" 
3. Select your preferred tool and level
4. Build normally - obfuscation happens automatically

### 🛡️ Antivirus Whitelist Generation

**What it does:** Generates comprehensive whitelist information to help with antivirus false positives.

**Generated Information:**
- 📋 File hashes (MD5, SHA1, SHA256, SHA512)
- 📊 File metadata and signatures
- 📝 Step-by-step whitelist instructions for major antivirus software
- 🔧 Common exclusion patterns

**Supported Antivirus Software:**
- Windows Defender
- Avast
- Norton
- McAfee
- And more...

**Usage:**
1. Enable "Generate Antivirus Whitelist"
2. Build your project
3. Find `*_whitelist_info.json` files in your output directory
4. Use the information to whitelist your executable

## ⚙️ Configuration

### Global Settings

Pro features can be configured in `auto_py_to_exe/config.py`:

```python
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
```

### Per-Project Settings

Pro features settings are saved in configuration files and can be imported/exported:

```json
{
  "version": "auto-py-to-exe-configuration_v1",
  "pyinstallerOptions": [...],
  "proFeatures": {
    "build_cache": true,
    "hidden_imports_detection": true,
    "obfuscation": false,
    "antivirus_whitelist": true,
    "obfuscation_tool": "pyarmor",
    "obfuscation_level": "medium"
  }
}
```

## 🔧 Troubleshooting

### Build Cache Issues

**Cache not working:**
- Check if `PRO_FEATURES_ENABLED = True` in config
- Verify cache directory permissions
- Clear cache and try again

**Cache taking too much space:**
- Reduce `BUILD_CACHE_MAX_SIZE_MB` in config
- Clear cache manually: click "Clear Cache" button

### Obfuscation Issues

**Obfuscation tool not found:**
- Install the tool: `pip install pyarmor`
- Check tool availability in Pro Features status

**Obfuscated code not working:**
- Try a lower obfuscation level
- Check for dynamic imports in your code
- Some libraries may not work with obfuscation

### Hidden Imports Issues

**Imports not detected:**
- Increase `HIDDEN_IMPORTS_SCAN_DEPTH` in config
- Add custom modules to `HIDDEN_IMPORTS_COMMON_MODULES`
- Manually add missing imports in PyInstaller options

## 📊 Performance Tips

1. **Enable build caching** for development workflows
2. **Use hidden imports detection** to reduce trial-and-error
3. **Start with low obfuscation** and increase gradually
4. **Monitor cache size** to prevent disk space issues

## 🤝 Contributing

To contribute to pro features:

1. Fork the repository
2. Create a feature branch
3. Add your enhancements to the pro features modules
4. Test thoroughly
5. Submit a pull request

## 📄 License

Pro features are part of auto-py-to-exe and follow the same MIT license.

## 🆘 Support

For issues with pro features:

1. Check this documentation
2. Review the troubleshooting section
3. Open an issue on GitHub with:
   - Pro features status from the UI
   - Error messages
   - Steps to reproduce

---

**Happy building with auto-py-to-exe Pro Features! 🚀**
