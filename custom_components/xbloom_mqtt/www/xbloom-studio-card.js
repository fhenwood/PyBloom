/**
 * XBloom Studio Card - Custom Lovelace Card
 * A sleek dashboard card for XBloom coffee machine control
 * 
 * Auto-discovers entities from the xbloom_mqtt integration
 */

class XBloomStudioCard extends HTMLElement {

  static get version() { return '1.0.0'; }

  // Card configuration
  static getConfigElement() {
    return document.createElement('xbloom-studio-card-editor');
  }

  static getStubConfig() {
    return {};
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._initialized) {
      this._initialize();
    }
    this._updateCard();
  }

  setConfig(config) {
    this._config = config;
  }

  getCardSize() {
    return 8;
  }

  _initialize() {
    this._initialized = true;

    // Create shadow DOM for style isolation
    const shadow = this.attachShadow({ mode: 'open' });

    // Styles
    const style = document.createElement('style');
    style.textContent = `
      :host {
        --xb-bg-primary: #151517;
        --xb-bg-card: #1c1c1e;
        --xb-bg-elevated: #2a2a2e;
        --xb-text-primary: #ffffff;
        --xb-text-secondary: rgba(255, 255, 255, 0.7);
        --xb-text-disabled: rgba(255, 255, 255, 0.4);
        --xb-accent: #e8e8e8;
        --xb-success: #4ade80;
        --xb-error: #ef4444;
        --xb-border: rgba(255, 255, 255, 0.08);
        --xb-radius: 16px;
      }

      .card {
        background: var(--xb-bg-card);
        border-radius: var(--xb-radius);
        padding: 20px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: var(--xb-text-primary);
        border: 1px solid var(--xb-border);
      }

      .card.disconnected .requires-connection {
        opacity: 0.4;
        filter: grayscale(100%);
        pointer-events: none;
      }

      /* Header */
      .header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 16px;
      }

      .header-left h1 {
        margin: 0;
        font-size: 24px;
        font-weight: 600;
      }

      .status {
        font-size: 14px;
        margin-top: 4px;
        text-transform: capitalize;
      }

      .status.connected { color: var(--xb-success); }
      .status.disconnected { color: var(--xb-error); }

      .machine-icon {
        width: 60px;
        height: 60px;
        opacity: 0.6;
      }

      /* Connect Button */
      .connect-btn {
        width: 100%;
        padding: 12px 24px;
        border: none;
        border-radius: 10px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        margin-bottom: 16px;
        transition: all 0.2s ease;
      }

      .connect-btn.connected {
        background: rgba(74, 222, 128, 0.15);
        color: var(--xb-success);
      }

      .connect-btn.disconnected {
        background: rgba(255, 255, 255, 0.1);
        color: var(--xb-text-secondary);
      }

      .connect-btn:hover {
        transform: scale(1.02);
      }

      /* Action Buttons Grid */
      .actions-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-bottom: 16px;
      }

      .action-btn {
        background: var(--xb-bg-elevated);
        border: 1px solid var(--xb-border);
        border-radius: var(--xb-radius);
        padding: 24px 16px;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease;
      }

      .action-btn:hover {
        background: rgba(255, 255, 255, 0.1);
      }

      .action-btn:active {
        transform: scale(0.98);
      }

      .action-btn .icon {
        font-size: 32px;
        margin-bottom: 8px;
        display: block;
      }

      .action-btn .label {
        font-size: 16px;
        font-weight: 500;
      }

      /* Sliders Section */
      .sliders-section {
        background: var(--xb-bg-elevated);
        border: 1px solid var(--xb-border);
        border-radius: var(--xb-radius);
        padding: 16px 20px;
        margin-bottom: 16px;
      }

      .slider-row {
        display: flex;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid var(--xb-border);
      }

      .slider-row:last-child {
        border-bottom: none;
      }

      .slider-icon {
        width: 24px;
        margin-right: 12px;
        opacity: 0.6;
      }

      .slider-label {
        flex: 0 0 60px;
        font-size: 14px;
        color: var(--xb-text-secondary);
      }

      .slider-input {
        flex: 1;
        -webkit-appearance: none;
        appearance: none;
        height: 4px;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 2px;
        margin: 0 16px;
      }

      .slider-input::-webkit-slider-thumb {
        -webkit-appearance: none;
        appearance: none;
        width: 16px;
        height: 16px;
        background: var(--xb-accent);
        border-radius: 50%;
        cursor: pointer;
      }

      .slider-value {
        flex: 0 0 60px;
        text-align: right;
        font-weight: 500;
        font-size: 14px;
      }

      /* Recipe Section */
      .recipe-section {
        margin-bottom: 16px;
      }

      .recipe-header {
        background: var(--xb-bg-elevated);
        border: 1px solid var(--xb-border);
        border-bottom: none;
        border-radius: var(--xb-radius) var(--xb-radius) 0 0;
        padding: 16px 20px 8px 20px;
      }

      .recipe-header h3 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
      }

      .recipe-select-wrapper {
        background: var(--xb-bg-elevated);
        border-left: 1px solid var(--xb-border);
        border-right: 1px solid var(--xb-border);
        padding: 8px 20px;
      }

      .recipe-select {
        width: 100%;
        padding: 12px 16px;
        background: var(--xb-bg-card);
        border: 1px solid var(--xb-border);
        border-radius: 10px;
        color: var(--xb-text-primary);
        font-size: 14px;
        cursor: pointer;
      }

      .pour-btn {
        display: block;
        width: calc(100% - 40px);
        margin: 0 20px 20px 20px;
        padding: 14px;
        background: rgba(255, 255, 255, 0.1);
        border: none;
        border-radius: 0 0 var(--xb-radius) var(--xb-radius);
        color: var(--xb-text-primary);
        font-size: 16px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
      }

      .pour-btn:hover {
        background: rgba(255, 255, 255, 0.15);
      }

      /* Footer - Sensors */
      .footer-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-bottom: 16px;
      }

      .sensor-card {
        background: var(--xb-bg-elevated);
        border: 1px solid var(--xb-border);
        border-radius: var(--xb-radius);
        padding: 16px 20px;
      }

      .sensor-card h4 {
        margin: 0 0 12px 0;
        font-size: 16px;
        font-weight: 600;
      }

      .sensor-row {
        display: flex;
        justify-content: space-between;
        margin: 8px 0;
        font-size: 14px;
      }

      .sensor-row .label {
        color: var(--xb-text-secondary);
      }

      .sensor-row .value {
        font-weight: 500;
      }

      .sensor-row .value.connected { color: var(--xb-success); }
      .sensor-row .value.disconnected { color: var(--xb-error); }

      /* Cancel Button */
      .cancel-btn {
        width: 100%;
        padding: 14px;
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: var(--xb-radius);
        color: var(--xb-error);
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        transition: all 0.2s ease;
      }

      .cancel-btn:hover {
        background: rgba(239, 68, 68, 0.25);
      }
    `;

    // Card container
    this._container = document.createElement('div');
    this._container.className = 'card';

    shadow.appendChild(style);
    shadow.appendChild(this._container);
  }

  _findEntity(type, suffix) {
    // Try different naming patterns - HA uses various formats
    const patterns = [
      `${type}.xbloom_coffee_machine_${suffix}`,
      `${type}.xbloom_${suffix}`,
      `${type}.xbloom_mqtt_${suffix}`,
      `${type}.xbloom_studio_${suffix}`,
    ];

    for (const pattern of patterns) {
      const entity = this._hass.states[pattern];
      if (entity) {
        return entity;
      }
    }

    // Fallback: search all entities for matching suffix
    const allEntities = Object.keys(this._hass.states).filter(
      id => id.startsWith(type + '.') && id.toLowerCase().includes('xbloom') && id.includes(suffix)
    );
    if (allEntities.length > 0) {
      return this._hass.states[allEntities[0]];
    }

    return null;
  }

  _getEntityId(type, suffix) {
    const entity = this._findEntity(type, suffix);
    if (entity) {
      return entity.entity_id;
    }
    // Fallback to default pattern
    return `${type}.xbloom_coffee_machine_${suffix}`;
  }

  _getEntityValue(entity, fallback = '--') {
    if (!entity) return fallback;
    if (entity.state === 'unavailable' || entity.state === 'unknown') return fallback;
    return entity.state;
  }

  _callService(domain, service, data) {
    this._hass.callService(domain, service, data);
  }

  _updateCard() {
    if (!this._container || !this._hass) return;

    // Get entities
    const status = this._findEntity('sensor', 'status');
    const weight = this._findEntity('sensor', 'weight');
    const error = this._findEntity('sensor', 'error');
    const grindSize = this._findEntity('number', 'grind_size');
    const rpm = this._findEntity('number', 'rpm');
    const temp = this._findEntity('number', 'temperature');
    const volume = this._findEntity('number', 'volume');
    const recipe = this._findEntity('select', 'recipe');

    const statusValue = this._getEntityValue(status, 'disconnected');
    const isConnected = statusValue === 'connected';
    const statusClass = isConnected ? 'connected' : 'disconnected';

    // Get recipe options
    const recipeOptions = recipe?.attributes?.options || ['No recipes'];

    // Get sensor values with fallbacks
    const weightValue = this._getEntityValue(weight, '0');
    const errorValue = this._getEntityValue(error, 'No errors');
    const grindValue = this._getEntityValue(grindSize, '50');
    const rpmValue = this._getEntityValue(rpm, '80');
    const tempValue = this._getEntityValue(temp, '92');
    const volumeValue = this._getEntityValue(volume, '200');

    this._container.className = `card ${statusClass}`;

    this._container.innerHTML = `
      <!-- Header -->
      <div class="header">
        <div class="header-left">
          <h1>XBloom Studio</h1>
          <div class="status ${statusClass}">${statusValue}</div>
        </div>
        <svg class="machine-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="8" y="4" width="32" height="40" rx="3"/>
          <rect x="12" y="8" width="24" height="20" rx="2" fill="rgba(255,255,255,0.1)"/>
          <line x1="16" y1="32" x2="32" y2="32"/>
          <line x1="16" y1="36" x2="32" y2="36"/>
          <circle cx="24" cy="40" r="2"/>
        </svg>
      </div>

      <!-- Connect Button -->
      <button class="connect-btn ${statusClass}" id="connect-btn">
        ${isConnected ? 'Disconnect' : 'Connect'}
      </button>

      <!-- Action Buttons -->
      <div class="actions-grid requires-connection">
        <button class="action-btn" id="grind-btn">
          <span class="icon">⚙️</span>
          <span class="label">Grind</span>
        </button>
        <button class="action-btn" id="brew-btn">
          <span class="icon">💧</span>
          <span class="label">Brew</span>
        </button>
      </div>

      <!-- Sliders -->
      <div class="sliders-section requires-connection">
        <div class="slider-row">
          <span class="slider-label">Grind</span>
          <input type="range" class="slider-input" id="grind-slider"
            min="${grindSize?.attributes?.min || 1}"
            max="${grindSize?.attributes?.max || 100}"
            value="${grindValue}">
          <span class="slider-value" id="grind-value">${grindValue}</span>
        </div>
        <div class="slider-row">
          <span class="slider-label">RPM</span>
          <input type="range" class="slider-input" id="rpm-slider"
            min="${rpm?.attributes?.min || 60}"
            max="${rpm?.attributes?.max || 100}"
            step="5"
            value="${rpmValue}">
          <span class="slider-value" id="rpm-value">${rpmValue}</span>
        </div>
        <div class="slider-row">
          <span class="slider-label">Temp</span>
          <input type="range" class="slider-input" id="temp-slider"
            min="${temp?.attributes?.min || 40}"
            max="${temp?.attributes?.max || 100}"
            value="${tempValue}">
          <span class="slider-value" id="temp-value">${tempValue}°C</span>
        </div>
        <div class="slider-row">
          <span class="slider-label">Volume</span>
          <input type="range" class="slider-input" id="volume-slider"
            min="${volume?.attributes?.min || 10}"
            max="${volume?.attributes?.max || 500}"
            step="10"
            value="${volumeValue}">
          <span class="slider-value" id="volume-value">${volumeValue} ml</span>
        </div>
      </div>

      <!-- Recipe I/O -->
      <div class="recipe-section requires-connection">
        <div class="recipe-header">
          <h3>Recipe I/O</h3>
        </div>
        <div class="recipe-select-wrapper">
          <select class="recipe-select" id="recipe-select">
            ${recipeOptions.map(opt => `<option value="${opt}" ${opt === recipe?.state ? 'selected' : ''}>${opt}</option>`).join('')}
          </select>
        </div>
        <button class="pour-btn" id="pour-btn">▶ Pour</button>
      </div>

      <!-- Sensors -->
      <div class="footer-grid">
        <div class="sensor-card">
          <h4>Sensors</h4>
          <div class="sensor-row">
            <span class="label">Weight</span>
            <span class="value">${weightValue} g</span>
          </div>
          <div class="sensor-row">
            <span class="label">Status</span>
            <span class="value ${statusClass}">${statusValue}</span>
          </div>
          <div class="sensor-row">
            <span class="label">Error</span>
            <span class="value">${errorValue}</span>
          </div>
        </div>
        <div class="sensor-card">
          <h4>Activity</h4>
          <div class="sensor-row">
            <span class="label" style="color: rgba(255,255,255,0.9)">XBloom Event</span>
          </div>
          <div class="sensor-row">
            <span class="label">Check logbook</span>
          </div>
        </div>
      </div>

      <!-- Cancel Button -->
      <button class="cancel-btn" id="cancel-btn">
        ⏹ Cancel All Operations
      </button>
    `;

    // Add event listeners
    this._attachEventListeners();
  }

  _attachEventListeners() {
    const shadow = this.shadowRoot;

    // Connect button
    shadow.getElementById('connect-btn')?.addEventListener('click', () => {
      this._callService('button', 'press', {
        entity_id: this._getEntityId('button', 'connect')
      });
    });

    // Grind button
    shadow.getElementById('grind-btn')?.addEventListener('click', () => {
      this._callService('button', 'press', {
        entity_id: this._getEntityId('button', 'grind')
      });
    });

    // Brew button
    shadow.getElementById('brew-btn')?.addEventListener('click', () => {
      this._callService('button', 'press', {
        entity_id: this._getEntityId('button', 'pour')
      });
    });

    // Pour/Execute recipe button
    shadow.getElementById('pour-btn')?.addEventListener('click', () => {
      this._callService('button', 'press', {
        entity_id: this._getEntityId('button', 'execute_recipe')
      });
    });

    // Cancel button
    shadow.getElementById('cancel-btn')?.addEventListener('click', () => {
      if (confirm('Stop all XBloom operations?')) {
        this._callService('button', 'press', {
          entity_id: this._getEntityId('button', 'cancel')
        });
      }
    });

    // Sliders
    const sliderConfig = [
      { id: 'grind-slider', valueId: 'grind-value', entity: 'grind_size', suffix: '' },
      { id: 'rpm-slider', valueId: 'rpm-value', entity: 'rpm', suffix: '' },
      { id: 'temp-slider', valueId: 'temp-value', entity: 'temperature', suffix: '°C' },
      { id: 'volume-slider', valueId: 'volume-value', entity: 'volume', suffix: ' ml' },
    ];

    sliderConfig.forEach(({ id, valueId, entity, suffix }) => {
      const slider = shadow.getElementById(id);
      const valueDisplay = shadow.getElementById(valueId);

      if (slider) {
        slider.addEventListener('input', (e) => {
          if (valueDisplay) valueDisplay.textContent = e.target.value + suffix;
        });

        slider.addEventListener('change', (e) => {
          this._callService('number', 'set_value', {
            entity_id: this._getEntityId('number', entity),
            value: parseFloat(e.target.value)
          });
        });
      }
    });

    // Recipe select
    shadow.getElementById('recipe-select')?.addEventListener('change', (e) => {
      this._callService('select', 'select_option', {
        entity_id: this._getEntityId('select', 'recipe'),
        option: e.target.value
      });
    });
  }
}

// Register the card
customElements.define('xbloom-studio-card', XBloomStudioCard);

// Register with Home Assistant's custom card picker
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'xbloom-studio-card',
  name: 'XBloom Studio',
  description: 'A sleek control card for XBloom coffee machines',
  preview: true,
});

console.info('%c XBLOOM-STUDIO-CARD %c v1.0.0 ',
  'color: white; background: #1c1c1e; font-weight: bold;',
  'color: #1c1c1e; background: #4ade80; font-weight: bold;'
);
