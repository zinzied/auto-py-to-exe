/*
Pro Features JavaScript Module - UI Integration
Handles pro features UI interactions and switch functionality.
*/

let proFeaturesEnabled = {
  buildCache: false,
  hiddenImports: false,
  obfuscation: false,
  antivirusWhitelist: false
};

// Initialize pro features UI interactions
const initializeProFeatures = () => {
  console.log('Pro features: UI initialization started');

  // Setup switch event listeners
  setupProFeaturesSwitches();

  console.log('Pro features: UI initialization completed');
};

// Setup event listeners for all pro features switches
const setupProFeaturesSwitches = () => {
  // Build Cache Switch
  const buildCacheSwitch = document.getElementById('build-cache-switch');
  if (buildCacheSwitch) {
    buildCacheSwitch.addEventListener('click', () => {
      toggleProFeature('buildCache', 'cache-stats-container', buildCacheSwitch);
    });
  }

  // Hidden Imports Switch
  const hiddenImportsSwitch = document.getElementById('hidden-imports-switch');
  if (hiddenImportsSwitch) {
    hiddenImportsSwitch.addEventListener('click', () => {
      toggleProFeature('hiddenImports', 'hidden-imports-container', hiddenImportsSwitch);
    });
  }

  // Obfuscation Switch
  const obfuscationSwitch = document.getElementById('obfuscation-switch');
  if (obfuscationSwitch) {
    obfuscationSwitch.addEventListener('click', () => {
      toggleProFeature('obfuscation', 'obfuscation-container', obfuscationSwitch);
    });
  }

  // Antivirus Whitelist Switch
  const antivirusSwitch = document.getElementById('antivirus-whitelist-switch');
  if (antivirusSwitch) {
    antivirusSwitch.addEventListener('click', () => {
      toggleProFeature('antivirusWhitelist', null, antivirusSwitch);
    });
  }

  // Clear Cache Button
  const clearCacheBtn = document.getElementById('clear-cache-btn');
  if (clearCacheBtn) {
    clearCacheBtn.addEventListener('click', () => {
      if (confirm('Clear build cache? (Feature not available yet)')) {
        updateCacheStats();
      }
    });
  }

  // Detect Imports Button
  const detectImportsBtn = document.getElementById('detect-imports-btn');
  if (detectImportsBtn) {
    detectImportsBtn.addEventListener('click', () => {
      const scriptPath = document.getElementById('entry-script')?.value;
      if (!scriptPath) {
        alert('Please select a script file first');
        return;
      }
      detectHiddenImports(scriptPath);
    });
  }
};

// Toggle a pro feature on/off
const toggleProFeature = (featureName, containerId, switchElement) => {
  const isEnabled = proFeaturesEnabled[featureName];
  proFeaturesEnabled[featureName] = !isEnabled;

  // Update switch text and style
  if (switchElement) {
    if (proFeaturesEnabled[featureName]) {
      switchElement.textContent = 'Disable';
      switchElement.classList.add('enabled');
    } else {
      switchElement.textContent = 'Enable';
      switchElement.classList.remove('enabled');
    }
  }

  // Show/hide associated container
  if (containerId) {
    const container = document.getElementById(containerId);
    if (container) {
      container.style.display = proFeaturesEnabled[featureName] ? 'block' : 'none';
    }
  }

  // Update status
  updateProFeaturesStatus();

  console.log(`Pro feature '${featureName}' ${proFeaturesEnabled[featureName] ? 'enabled' : 'disabled'}`);
};

// Show a simple message when pro features are not available
const showProFeaturesUnavailable = () => {
  const proSection = document.getElementById('pro-features-section');
  if (proSection) {
    proSection.style.display = 'block';
    proSection.innerHTML = `
      <div class="header" style="cursor: pointer;">
        <img src="/img/chevron-square-up.svg" alt="Toggle" />
        <h2>🚀 Pro Features</h2>
      </div>
      <div class="content" style="display: none;">
        <div class="pro-feature-group">
          <h3>ℹ️ Information</h3>
          <div class="pro-feature-item">
            <div class="feature-description">
              Pro features are not available. To enable pro features, install the required dependencies:
              <br><br>
              <code>python install_pro_features.py</code>
            </div>
          </div>
        </div>
      </div>
    `;

    // Add toggle functionality
    const header = proSection.querySelector('.header');
    if (header) {
      header.addEventListener('click', () => {
        const chevron = proSection.querySelector('.header img');
        const content = proSection.querySelector('.content');

        if (proSection.getAttribute('data-expanded') === null) {
          chevron.style.transform = 'rotate(0deg)';
          content.style.display = 'block';
          proSection.setAttribute('data-expanded', '');
        } else {
          chevron.style.transform = 'rotate(180deg)';
          content.style.display = 'none';
          proSection.removeAttribute('data-expanded');
        }
      });
    }
  }
};

// Setup the pro features UI
const setupProFeaturesUI = () => {
  const proSection = document.getElementById('pro-features-section');
  if (proSection) {
    proSection.style.display = 'block';

    // Setup section toggle functionality (like other sections)
    const header = proSection.querySelector('.header');
    if (header) {
      header.addEventListener('click', () => {
        const chevron = proSection.querySelector('.header img');
        const content = proSection.querySelector('.content');

        if (proSection.getAttribute('data-expanded') === null) {
          // Show the section
          chevron.style.transform = 'rotate(0deg)';
          content.style.display = 'block';
          proSection.setAttribute('data-expanded', '');
        } else {
          // Hide the section
          chevron.style.transform = 'rotate(180deg)';
          content.style.display = 'none';
          proSection.removeAttribute('data-expanded');
        }
      });

      // Make header clickable
      header.style.cursor = 'pointer';
    }

    // Update status display
    updateProFeaturesStatus();
  }
};

// Load current pro features settings
const loadProFeaturesSettings = () => {
  if (!proFeaturesData || !proFeaturesData.features) return;

  // Load checkbox states
  document.getElementById('build-cache-enabled').checked = proFeaturesData.features.build_cache;
  document.getElementById('hidden-imports-enabled').checked = proFeaturesData.features.hidden_imports_detection;
  document.getElementById('obfuscation-enabled').checked = proFeaturesData.features.obfuscation;
  document.getElementById('antivirus-whitelist-enabled').checked = proFeaturesData.features.antivirus_whitelist;

  // Load obfuscation settings
  document.getElementById('obfuscation-tool').value = proFeaturesData.obfuscation_tool || 'pyarmor';
  document.getElementById('obfuscation-level').value = proFeaturesData.obfuscation_level || 'medium';
};

// Setup event listeners for pro features
const setupProFeaturesEventListeners = () => {
  // Build cache events
  document.getElementById('build-cache-enabled').addEventListener('change', async (e) => {
    await updateProFeatureSetting('build_cache', e.target.checked);
    if (e.target.checked) {
      updateCacheStats();
    }
  });

  document.getElementById('clear-cache-btn').addEventListener('click', async () => {
    if (confirm('Are you sure you want to clear the build cache?')) {
      const success = await eel.clear_build_cache()();
      if (success) {
        updateCacheStats();
      }
    }
  });

  // Hidden imports events
  document.getElementById('hidden-imports-enabled').addEventListener('change', async (e) => {
    await updateProFeatureSetting('hidden_imports_detection', e.target.checked);
  });

  document.getElementById('detect-imports-btn').addEventListener('click', async () => {
    const scriptPath = document.getElementById('entry-script').value;
    if (!scriptPath) {
      alert('Please select a script file first');
      return;
    }

    const imports = await eel.detect_hidden_imports(scriptPath)();
    displayDetectedImports(imports);
  });

  // Obfuscation events
  document.getElementById('obfuscation-enabled').addEventListener('change', async (e) => {
    await updateProFeatureSetting('obfuscation', e.target.checked);
    if (e.target.checked) {
      checkObfuscationAvailability();
    }
  });

  document.getElementById('obfuscation-tool').addEventListener('change', async (e) => {
    await updateObfuscationSettings();
    checkObfuscationAvailability();
  });

  document.getElementById('obfuscation-level').addEventListener('change', async (e) => {
    await updateObfuscationSettings();
  });

  // Antivirus whitelist events
  document.getElementById('antivirus-whitelist-enabled').addEventListener('change', async (e) => {
    await updateProFeatureSetting('antivirus_whitelist', e.target.checked);
  });
};

// Update a pro feature setting
const updateProFeatureSetting = async (feature, enabled) => {
  try {
    const success = await eel.update_pro_feature_setting(feature, enabled)();
    if (success) {
      console.log(`Pro feature '${feature}' ${enabled ? 'enabled' : 'disabled'}`);
      updateProFeaturesStatus();
    }
  } catch (error) {
    console.error(`Failed to update ${feature}:`, error);
  }
};

// Update obfuscation settings
const updateObfuscationSettings = async () => {
  try {
    const tool = document.getElementById('obfuscation-tool').value;
    const level = document.getElementById('obfuscation-level').value;

    const success = await eel.update_obfuscation_settings(tool, level)();
    if (success) {
      console.log(`Obfuscation settings updated: ${tool} (${level})`);
    }
  } catch (error) {
    console.error('Failed to update obfuscation settings:', error);
  }
};

// Update cache statistics display
const updateCacheStats = async () => {
  try {
    if (!window.eel || !window.eel.get_build_cache_stats) {
      return;
    }

    const stats = await eel.get_build_cache_stats()();
    const cacheStatsDiv = document.getElementById('cache-stats');

    if (!cacheStatsDiv) return;

    if (stats && Object.keys(stats).length > 0) {
      cacheStatsDiv.innerHTML = `
        <div>📊 Cache Stats:</div>
        <div>• Entries: ${stats.total_entries}</div>
        <div>• Size: ${stats.total_size_mb} MB / ${stats.max_size_mb} MB</div>
        <div>• Retention: ${stats.retention_days} days</div>
      `;
    } else {
      cacheStatsDiv.innerHTML = '<div>📊 Cache: Empty</div>';
    }
  } catch (error) {
    console.error('Failed to get cache stats:', error);
    const cacheStatsDiv = document.getElementById('cache-stats');
    if (cacheStatsDiv) {
      cacheStatsDiv.innerHTML = '<div>❌ Cache stats unavailable</div>';
    }
  }
};

// Check obfuscation tool availability
const checkObfuscationAvailability = async () => {
  try {
    if (!window.eel || !window.eel.check_obfuscation_availability) {
      return;
    }

    const result = await eel.check_obfuscation_availability()();
    const statusDiv = document.getElementById('obfuscation-status');

    if (!statusDiv) return;

    if (result && result.available) {
      statusDiv.innerHTML = `<div class="feature-status success">✅ ${result.message}</div>`;
    } else {
      statusDiv.innerHTML = `<div class="feature-status error">❌ ${result ? result.message : 'Not available'}</div>`;
    }
  } catch (error) {
    console.error('Failed to check obfuscation availability:', error);
    const statusDiv = document.getElementById('obfuscation-status');
    if (statusDiv) {
      statusDiv.innerHTML = '<div class="feature-status error">❌ Error checking availability</div>';
    }
  }
};

// Display detected imports
const displayDetectedImports = (imports) => {
  const importsDiv = document.getElementById('detected-imports');

  if (imports && imports.length > 0) {
    importsDiv.innerHTML = `
      <div>🔍 Detected ${imports.length} hidden imports:</div>
      <div>${imports.map(imp => `• ${imp}`).join('<br>')}</div>
    `;
  } else {
    importsDiv.innerHTML = '<div>🔍 No hidden imports detected</div>';
  }
};

// Update pro features status display
const updateProFeaturesStatus = () => {
  const statusDiv = document.getElementById('pro-features-status');

  if (proFeaturesData && proFeaturesData.available) {
    const features = proFeaturesData.features;
    const enabledCount = Object.values(features).filter(Boolean).length;
    const totalCount = Object.keys(features).length;

    statusDiv.innerHTML = `
      <div>🚀 Pro Features: ${enabledCount}/${totalCount} enabled</div>
      <div>• Build Cache: ${features.build_cache ? '✅' : '❌'}</div>
      <div>• Hidden Imports: ${features.hidden_imports_detection ? '✅' : '❌'}</div>
      <div>• Obfuscation: ${features.obfuscation ? '✅' : '❌'}</div>
      <div>• Antivirus Whitelist: ${features.antivirus_whitelist ? '✅' : '❌'}</div>
    `;
  } else {
    statusDiv.innerHTML = '<div>❌ Pro features not available</div>';
  }
};

// Add pro features info to configuration export
const addProFeaturesToConfiguration = (config) => {
  if (proFeaturesData && proFeaturesData.available) {
    config.proFeatures = {
      build_cache: document.getElementById('build-cache-enabled').checked,
      hidden_imports_detection: document.getElementById('hidden-imports-enabled').checked,
      obfuscation: document.getElementById('obfuscation-enabled').checked,
      antivirus_whitelist: document.getElementById('antivirus-whitelist-enabled').checked,
      obfuscation_tool: document.getElementById('obfuscation-tool').value,
      obfuscation_level: document.getElementById('obfuscation-level').value
    };
  }
  return config;
};

// Load pro features from configuration import
const loadProFeaturesFromConfiguration = (config) => {
  if (config.proFeatures && proFeaturesData && proFeaturesData.available) {
    const pf = config.proFeatures;

    // Update checkboxes
    if (pf.build_cache !== undefined) {
      document.getElementById('build-cache-enabled').checked = pf.build_cache;
      updateProFeatureSetting('build_cache', pf.build_cache);
    }

    if (pf.hidden_imports_detection !== undefined) {
      document.getElementById('hidden-imports-enabled').checked = pf.hidden_imports_detection;
      updateProFeatureSetting('hidden_imports_detection', pf.hidden_imports_detection);
    }

    if (pf.obfuscation !== undefined) {
      document.getElementById('obfuscation-enabled').checked = pf.obfuscation;
      updateProFeatureSetting('obfuscation', pf.obfuscation);
    }

    if (pf.antivirus_whitelist !== undefined) {
      document.getElementById('antivirus-whitelist-enabled').checked = pf.antivirus_whitelist;
      updateProFeatureSetting('antivirus_whitelist', pf.antivirus_whitelist);
    }

    // Update obfuscation settings
    if (pf.obfuscation_tool) {
      document.getElementById('obfuscation-tool').value = pf.obfuscation_tool;
    }

    if (pf.obfuscation_level) {
      document.getElementById('obfuscation-level').value = pf.obfuscation_level;
    }

    if (pf.obfuscation_tool || pf.obfuscation_level) {
      updateObfuscationSettings();
    }
  }
};

// Update cache statistics display
const updateCacheStats = () => {
  const cacheStatsDiv = document.getElementById('cache-stats');
  if (cacheStatsDiv) {
    if (proFeaturesEnabled.buildCache) {
      cacheStatsDiv.innerHTML = '📊 Cache: Feature not available yet<br>Install dependencies to enable';
    } else {
      cacheStatsDiv.innerHTML = '📊 Cache: Disabled';
    }
  }
};

// Detect hidden imports (placeholder)
const detectHiddenImports = (scriptPath) => {
  const importsDiv = document.getElementById('detected-imports');
  if (importsDiv) {
    importsDiv.innerHTML = `🔍 Scanning ${scriptPath}...<br>Feature not available yet<br>Install dependencies to enable`;
  }
};

// Update pro features status display
const updateProFeaturesStatus = () => {
  const statusDiv = document.getElementById('pro-features-status');
  if (statusDiv) {
    const enabledCount = Object.values(proFeaturesEnabled).filter(Boolean).length;
    const totalCount = Object.keys(proFeaturesEnabled).length;

    statusDiv.innerHTML = `
      🚀 Pro Features: ${enabledCount}/${totalCount} enabled<br>
      • Build Cache: ${proFeaturesEnabled.buildCache ? '✅' : '❌'}<br>
      • Hidden Imports: ${proFeaturesEnabled.hiddenImports ? '✅' : '❌'}<br>
      • Obfuscation: ${proFeaturesEnabled.obfuscation ? '✅' : '❌'}<br>
      • Antivirus Whitelist: ${proFeaturesEnabled.antivirusWhitelist ? '✅' : '❌'}<br><br>
      ❌ Pro features not fully available yet.<br>
      To enable full functionality, install dependencies:<br>
      <code>python install_pro_features.py</code>
    `;
  }
};

// Configuration export/import functions
const addProFeaturesToConfiguration = (config) => {
  config.proFeatures = {
    buildCache: proFeaturesEnabled.buildCache,
    hiddenImports: proFeaturesEnabled.hiddenImports,
    obfuscation: proFeaturesEnabled.obfuscation,
    antivirusWhitelist: proFeaturesEnabled.antivirusWhitelist
  };
  return config;
};

const loadProFeaturesFromConfiguration = (config) => {
  if (config.proFeatures) {
    const pf = config.proFeatures;

    // Update enabled states
    if (pf.buildCache !== undefined) {
      proFeaturesEnabled.buildCache = pf.buildCache;
      updateSwitchState('build-cache-switch', 'cache-stats-container', pf.buildCache);
    }

    if (pf.hiddenImports !== undefined) {
      proFeaturesEnabled.hiddenImports = pf.hiddenImports;
      updateSwitchState('hidden-imports-switch', 'hidden-imports-container', pf.hiddenImports);
    }

    if (pf.obfuscation !== undefined) {
      proFeaturesEnabled.obfuscation = pf.obfuscation;
      updateSwitchState('obfuscation-switch', 'obfuscation-container', pf.obfuscation);
    }

    if (pf.antivirusWhitelist !== undefined) {
      proFeaturesEnabled.antivirusWhitelist = pf.antivirusWhitelist;
      updateSwitchState('antivirus-whitelist-switch', null, pf.antivirusWhitelist);
    }

    updateProFeaturesStatus();
  }
};

// Helper function to update switch state
const updateSwitchState = (switchId, containerId, enabled) => {
  const switchElement = document.getElementById(switchId);
  if (switchElement) {
    switchElement.textContent = enabled ? 'Disable' : 'Enable';
    if (enabled) {
      switchElement.classList.add('enabled');
    } else {
      switchElement.classList.remove('enabled');
    }
  }

  if (containerId) {
    const container = document.getElementById(containerId);
    if (container) {
      container.style.display = enabled ? 'block' : 'none';
    }
  }
};

// Export functions for use in other modules
window.proFeatures = {
  initialize: initializeProFeatures,
  addToConfiguration: addProFeaturesToConfiguration,
  loadFromConfiguration: loadProFeaturesFromConfiguration,
  updateCacheStats: updateCacheStats
};
