

let sidebarVisible = true;
let sidebarMaximized = false;
let maximizedPanelId = null;
const TERMINAL_PANEL_ID = 'terminal';
const CODE_PANEL_ID = 'vscode';
const REDIS_INSIGHT_PANEL_ID = 'redisinsight';
const RIGHT_PANEL_MAX_VISIBLE = 3;
const TERMINAL_MAX_TABS = 4;
const TRACK_STORAGE_KEY = 'bank-iris-active-track';
const TRACKS = ['python'];
const DEFAULT_TRACK = 'python';
const CODE_SERVER_BASE_ROOT = '/home/coder/code';
const CODE_FILE_PATTERN = /^(?:code\/(python|java)\/)?(src\/.+|build\.gradle\.kts)$/;
const CODE_OPEN_BRIDGE_URL = '/vscode/proxy/47777/open-file';
const REDIS_INSIGHT_HEALTH_URL = '/redisinsight/api/health';
const REDIS_INSIGHT_DATABASES_URL = '/redisinsight/api/databases';
const REDIS_INSIGHT_DATABASE_NAME = 'Workshop Redis';
const REDIS_INSIGHT_READY_RETRY_MS = 1000;
const TERMINAL_RESTART_ENDPOINT = '/app/terminal/restart';
const CODE_OPEN_BRIDGE_TIMEOUT_MS = 8000;
const IFRAME_POINTER_RESTORE_MS = 2500;
const PANEL_READY_RETRY_MS = 1000;
const RESTART_STATUS_POLL_MS = 1000;
let terminalTabs = [{ id: 0 }];
let activeTerminalTabId = 0;
let restartTerminalTabId = null;
let restartCommandActive = false;
let restartStatusPollTimer = null;
let panelLoadersStarted = false;
let iframePointerRestoreTimer = null;
let isResizingPanels = false;
let activeRightPanelId = '';
let pinnedRightPanelIds = [];
let rightPanelNoticeTimer = null;

function normalizeTrack(value) {
  const track = String(value || '').trim().toLowerCase();
  return TRACKS.includes(track) ? track : '';
}

function readActiveTrack() {
  try {
    return normalizeTrack(localStorage.getItem(TRACK_STORAGE_KEY)) || DEFAULT_TRACK;
  } catch (_error) {
    return DEFAULT_TRACK;
  }
}

function storeActiveTrack(track) {
  const nextTrack = normalizeTrack(track);
  if (!nextTrack) return;

  try {
    localStorage.setItem(TRACK_STORAGE_KEY, nextTrack);
  } catch (_error) {
    // Storage is only used to keep the browser panels aligned.
  }
}

function codeServerRoot(track = '') {
  const selectedTrack = normalizeTrack(track) || readActiveTrack();
  return selectedTrack ? `${CODE_SERVER_BASE_ROOT}/${selectedTrack}` : CODE_SERVER_BASE_ROOT;
}

function codePanelPath(track) {
  return `/vscode/?folder=${codeServerRoot(track)}`;
}

function resolvePanelUrl(panel) {
  if (isTerminalPanel(panel)) return terminalTabPath(activeTerminalTabId);
  if (panel.id === CODE_PANEL_ID) return codePanelPath();
  return panel.path;
}

function isRedisInsightPanel(panelId) {
  return panelId === REDIS_INSIGHT_PANEL_ID;
}

function isRedisInsightUrl(url = '') {
  return String(url).startsWith('/redisinsight/');
}

function uniquePanelIds(panelIds = []) {
  return [...new Set(panelIds.filter(panelId => Boolean(rightPanelById(panelId))))];
}

function rightPanelById(panelId) {
  return config.panels.find(panel => panel.id === panelId) || null;
}

function defaultRightPanelId() {
  return config.panels.find(panel => panel.visible !== false)?.id || config.panels[0]?.id || '';
}

function visibleRightPanelIds() {
  return uniquePanelIds([activeRightPanelId, ...pinnedRightPanelIds]).slice(0, RIGHT_PANEL_MAX_VISIBLE);
}

function visibleRightPanels() {
  const visibleIds = visibleRightPanelIds();
  return config.panels.filter(panel => visibleIds.includes(panel.id));
}

function visibleComponentCount(nextSidebarVisible = sidebarVisible) {
  return (nextSidebarVisible ? 1 : 0) + visibleRightPanels().length;
}

function setCheckboxChecked(id, checked) {
  const checkbox = document.getElementById(id);
  if (checkbox) checkbox.checked = checked;
}

function normalizeRightPanelState() {
  const fallbackPanelId = defaultRightPanelId();

  if (!rightPanelById(activeRightPanelId)) {
    activeRightPanelId = fallbackPanelId;
  }

  pinnedRightPanelIds = uniquePanelIds(pinnedRightPanelIds)
    .filter(panelId => panelId !== activeRightPanelId)
    .slice(0, RIGHT_PANEL_MAX_VISIBLE - 1);
}

function isTerminalPanel(panel) {
  return panel.id === TERMINAL_PANEL_ID;
}

function terminalTabPath(tabId) {
  return `/terminal/${tabId}/`;
}

function terminalTabLabel(tabId) {
  const tab = terminalTabs.find(candidate => candidate.id === tabId);
  return typeof tab?.label === 'string' && tab.label.trim() ? tab.label : 'Terminal';
}

function getActiveTerminalTab() {
  return terminalTabs.find(tab => tab.id === activeTerminalTabId) || terminalTabs[0];
}

function nextTerminalTabId() {
  for (let tabId = 0; tabId < TERMINAL_MAX_TABS; tabId++) {
    if (!terminalTabs.some(tab => tab.id === tabId)) {
      return tabId;
    }
  }
  return null;
}

function panelContentMarkup(panel, panelUrl) {
  if (!isTerminalPanel(panel)) {
    return `
      <div class="panel-content">
        <div class="panel-loading" data-url="${panelUrl}">
          <i class="fa-solid fa-spinner"></i>
          <span>Connecting...</span>
        </div>
        <iframe title="${panel.name}"></iframe>
      </div>
    `;
  }

  return `
    <div class="panel-content terminal-content">
      <div class="terminal-tabbar" role="tablist" aria-label="Terminal sessions"></div>
      <div class="terminal-frames"></div>
    </div>
  `;
}

// Initialize the workbench
function init() {
  // Set title from config
  document.getElementById('title').textContent = config.title;
  document.title = config.title;

  activeRightPanelId = defaultRightPanelId();
  pinnedRightPanelIds = [];
  normalizeRightPanelState();

  // Instructions are always visible; right-side resources are controlled by tabs.
  sidebarVisible = true;

  // Build the UI
  buildPanels();
  setupSidebarFrameMessages();
  setupIframePointerRecovery();
  setupResizers();
}

// Build panels from config
function buildPanels() {
  const main = document.getElementById('container');
  panelLoadersStarted = false;
  main.innerHTML = '';

  // Create sidebar once; visibility is handled with CSS so other iframes stay alive.
  const sidebarUrl = config.sidebar.path;
  const sidebar = document.createElement('aside');
  sidebar.id = 'sidebar';
  sidebar.className = 'panel';
  sidebar.innerHTML = `
      <div class="panel-header">
        <div class="panel-title-group">
          <span class="panel-title">${config.sidebar.name}</span>
        </div>
        <div class="panel-controls">
          <a class="panel-control-btn" href="${sidebarUrl}" target="_blank" rel="noopener noreferrer" title="Open in new tab">
            <i class="fa-solid fa-arrow-up-right-from-square"></i>
          </a>
          <button class="panel-control-btn sidebar-maximize-btn" type="button" title="Maximize ${config.sidebar.name}" aria-label="Maximize ${config.sidebar.name}" aria-pressed="false">
            <i class="fa-solid fa-expand"></i>
          </button>
          <button class="panel-control-btn sidebar-hide-btn" type="button" title="Hide ${config.sidebar.name}" aria-label="Hide ${config.sidebar.name}">
            <i class="fa-solid fa-eye-slash"></i>
          </button>
        </div>
      </div>
      <div class="panel-content">
        <div class="panel-loading" data-url="${sidebarUrl}">
          <i class="fa-solid fa-spinner"></i>
          <span>Connecting...</span>
        </div>
        <iframe title="${config.sidebar.name}"></iframe>
      </div>
    `;
  main.appendChild(sidebar);

  sidebar.querySelector('.sidebar-maximize-btn')?.addEventListener('click', () => {
    toggleSidebarMaximized();
  });
  sidebar.querySelector('.sidebar-hide-btn')?.addEventListener('click', () => {
    setSidebarVisible(false);
  });

  // Create vertical resizer
  const verticalResizer = document.createElement('div');
  verticalResizer.id = 'verticalResizer';
  verticalResizer.className = 'resizer resizer-vertical';
  verticalResizer.innerHTML = '<div class="resizer-handle"></div>';
  main.appendChild(verticalResizer);

  // Create right stack
  const rightStack = document.createElement('div');
  rightStack.className = 'right-stack';
  rightStack.id = 'rightStack';
  main.appendChild(rightStack);

  // Create panels in right stack
  buildRightStack();
}

// Build the right stack panels (called once during init)
function buildRightStack() {
  const rightStack = document.getElementById('rightStack');

  const tabs = document.createElement('div');
  tabs.id = 'rightPanelTabs';
  tabs.className = 'right-panel-tabs';
  tabs.innerHTML = `
    <div class="right-panel-tabs-row" role="tablist" aria-label="Resources"></div>
    <div class="right-panel-tabs-status" aria-live="polite"></div>
  `;
  rightStack.appendChild(tabs);

  // Create all panels (resizers are added dynamically based on visibility)
  config.panels.forEach((panel) => {
    // Create panel
    const panelUrl = resolvePanelUrl(panel);
    const section = document.createElement('section');
    section.id = `panel-${panel.id}`;
    section.className = `panel${isTerminalPanel(panel) ? ' terminal-panel' : ''}`;
    section.innerHTML = `
      <div class="panel-header panel-header--actions-only">
        <div class="panel-controls">
          <button class="panel-control-btn refresh-btn" data-panel="${panel.id}" title="Refresh ${panel.name}">
            <i class="fa-solid fa-rotate-right"></i>
          </button>
          <a class="panel-control-btn open-panel-btn" data-panel="${panel.id}" href="${panelUrl}" target="_blank" rel="noopener noreferrer" title="Open in new tab">
            <i class="fa-solid fa-arrow-up-right-from-square"></i>
          </a>
        </div>
      </div>
      ${panelContentMarkup(panel, panelUrl)}
    `;
    rightStack.appendChild(section);

    if (isTerminalPanel(panel)) {
      setupTerminalPanel(section);
    }
  });

  // Setup panel header buttons
  setupPanelHeaderButtons();
  // Setup resizers
  setupResizers();
  // Start checking for panel availability
  startPanelLoaders();
  // Apply initial visibility
  updatePanelVisibility();
}

// Update panel visibility using CSS (preserves iframes)
function updatePanelVisibility() {
  normalizeRightPanelState();
  updateComponentLayout();
  renderRightPanelTabs();

  config.panels.forEach((panel) => {
    const section = document.getElementById(`panel-${panel.id}`);
    if (!section) return;

    const isVisible = visibleRightPanelIds().includes(panel.id);
    const isMaximized = maximizedPanelId === panel.id;
    const shouldShow = isVisible && (!maximizedPanelId || isMaximized);

    // Show/hide panel
    section.style.display = shouldShow ? '' : 'none';
    section.classList.toggle('maximized', isMaximized);

    // Reset flex/height when shown so panels redistribute evenly
    if (shouldShow) {
      section.style.flex = '';
      section.style.height = '';
    }

  });

  // Rebuild resizers between visible adjacent panels
  rebuildHorizontalResizers();
}

function setRightPanelNotice(message = '') {
  const notice = document.querySelector('#rightPanelTabs .right-panel-tabs-status');
  window.clearTimeout(rightPanelNoticeTimer);

  if (!notice) return;

  notice.textContent = message;
  notice.classList.toggle('active', Boolean(message));

  if (message) {
    rightPanelNoticeTimer = window.setTimeout(() => {
      notice.textContent = '';
      notice.classList.remove('active');
    }, 2400);
  }
}

function activateRightPanel(panelId, options = {}) {
  if (!rightPanelById(panelId)) return;

  activeRightPanelId = panelId;
  pinnedRightPanelIds = uniquePanelIds(pinnedRightPanelIds).filter(id => id !== panelId);

  // Leave Instructions focus mode when a resource tab is activated
  // (including docs deep-links that open Code / App / Terminal / Insight).
  if (sidebarMaximized) {
    sidebarMaximized = false;
  }

  if (maximizedPanelId && maximizedPanelId !== panelId) {
    maximizedPanelId = null;
  }

  if (!options.silent) {
    setRightPanelNotice('');
  }

  if (panelId === CODE_PANEL_ID) {
    updateCodePanelUrl(document.getElementById(`panel-${panelId}`));
  }

  if (isRedisInsightPanel(panelId)) {
    ensureRedisInsightPanelLoaded(panelId);
  }

  updatePanelVisibility();
}

function toggleRightPanelPin(panelId) {
  const panel = rightPanelById(panelId);
  if (!panel) return;

  const existingIndex = pinnedRightPanelIds.indexOf(panelId);
  if (existingIndex >= 0) {
    pinnedRightPanelIds.splice(existingIndex, 1);
    if (maximizedPanelId === panelId) {
      maximizedPanelId = null;
    }
    setRightPanelNotice(`${panel.name} unpinned.`);
    updatePanelVisibility();
    return;
  }

  if (panelId === activeRightPanelId) {
    setRightPanelNotice(`${panel.name} is already active.`);
    return;
  }

  if (visibleRightPanelIds().length >= RIGHT_PANEL_MAX_VISIBLE) {
    setRightPanelNotice(`Maximum ${RIGHT_PANEL_MAX_VISIBLE} visible resources. Unpin one first.`);
    return;
  }

  pinnedRightPanelIds.push(panelId);
  setRightPanelNotice(`${panel.name} pinned.`);

  if (panelId === CODE_PANEL_ID) {
    updateCodePanelUrl(document.getElementById(`panel-${panelId}`));
  }

  if (isRedisInsightPanel(panelId)) {
    ensureRedisInsightPanelLoaded(panelId);
  }

  updatePanelVisibility();
}

function hideRightPanel(panelId) {
  const panel = rightPanelById(panelId);
  if (!panel) return;

  pinnedRightPanelIds = pinnedRightPanelIds.filter(id => id !== panelId);

  if (maximizedPanelId === panelId) {
    maximizedPanelId = null;
  }

  if (activeRightPanelId === panelId) {
    activeRightPanelId = pinnedRightPanelIds.shift()
      || config.panels.find(candidate => candidate.id !== panelId)?.id
      || panelId;
  }

  normalizeRightPanelState();
  setRightPanelNotice(`${panel.name} hidden.`);
  updatePanelVisibility();
}

function ensureRedisInsightPanelLoaded(panelId) {
  const section = document.getElementById(`panel-${panelId}`);
  const loadingEl = section?.querySelector('.panel-loading');
  const iframe = section?.querySelector('iframe');
  const currentSrc = iframe?.getAttribute('src') || '';

  if (loadingEl && iframe && !currentSrc) {
    loadRedisInsightPanel(loadingEl);
  }
}

function renderRightPanelTabs() {
  const tabs = document.querySelector('#rightPanelTabs .right-panel-tabs-row');
  if (!tabs) return;

  const visibleIds = visibleRightPanelIds();
  const showSidebarButton = !sidebarVisible
    ? `
      <button
        type="button"
        class="right-panel-show-sidebar"
        data-show-sidebar
        title="Show ${config.sidebar.name}"
        aria-label="Show ${config.sidebar.name}"
      >
        <i class="fa-solid ${config.sidebar.icon || 'fa-book'}"></i>
        <span>${config.sidebar.name}</span>
        <i class="fa-solid fa-eye"></i>
      </button>
    `
    : '';

  tabs.innerHTML = showSidebarButton + config.panels.map(panel => {
    const isActive = activeRightPanelId === panel.id;
    const isPinned = pinnedRightPanelIds.includes(panel.id);
    const pinDisabled = !isPinned && !isActive && visibleIds.length >= RIGHT_PANEL_MAX_VISIBLE;
    const pinLabel = `${isPinned ? 'Unpin' : 'Pin'} ${panel.name}`;

    return `
      <div class="right-panel-tab${isActive ? ' active' : ''}${isPinned ? ' pinned' : ''}" role="presentation">
        <button
          type="button"
          class="right-panel-tab-main"
          data-right-panel-tab="${panel.id}"
          role="tab"
          aria-selected="${isActive}"
        >
          <i class="fa-solid ${panel.icon}"></i>
          <span>${panel.name}</span>
        </button>
        <button
          type="button"
          class="right-panel-tab-pin${isPinned ? ' pinned' : ''}"
          data-right-panel-pin="${panel.id}"
          aria-label="${pinLabel}"
          title="${pinLabel}"
          ${pinDisabled ? 'disabled' : ''}
        >
          <i class="fa-solid fa-thumbtack"></i>
        </button>
      </div>
    `;
  }).join('');

  tabs.querySelector('[data-show-sidebar]')?.addEventListener('click', () => {
    setSidebarVisible(true);
  });

  tabs.querySelectorAll('[data-right-panel-tab]').forEach(button => {
    button.addEventListener('click', event => {
      if (event.target.closest('[data-right-panel-pin]')) return;
      activateRightPanel(button.dataset.rightPanelTab);
    });
  });

  tabs.querySelectorAll('[data-right-panel-pin]').forEach(button => {
    button.addEventListener('click', event => {
      event.preventDefault();
      event.stopPropagation();
      if (button.disabled) {
        setRightPanelNotice(`Maximum ${RIGHT_PANEL_MAX_VISIBLE} visible resources. Unpin one first.`);
        return;
      }
      toggleRightPanelPin(button.dataset.rightPanelPin);
    });
  });
}

// Rebuild horizontal resizers to connect only visible adjacent panels
function rebuildHorizontalResizers() {
  const rightStack = document.getElementById('rightStack');
  if (!rightStack) return;

  // Remove all existing horizontal resizers
  rightStack.querySelectorAll('.resizer-horizontal').forEach(r => r.remove());

  // Don't add resizers if a panel is maximized
  if (maximizedPanelId) return;

  // Get visible panels in config order
  const visiblePanels = visibleRightPanels();

  // Insert resizers between adjacent visible panels
  for (let i = 1; i < visiblePanels.length; i++) {
    const abovePanel = visiblePanels[i - 1];
    const belowPanel = visiblePanels[i];

    const resizer = document.createElement('div');
    resizer.className = 'resizer resizer-horizontal';
    resizer.dataset.above = abovePanel.id;
    resizer.dataset.below = belowPanel.id;
    resizer.innerHTML = '<div class="resizer-handle"></div>';

    // Insert before the below panel
    const belowSection = document.getElementById(`panel-${belowPanel.id}`);
    if (belowSection) {
      rightStack.insertBefore(resizer, belowSection);
    }
  }

  // Re-setup resizer event handlers
  setupHorizontalResizers();
}

function updateSidebarMaximizeButton() {
  const button = document.querySelector('.sidebar-maximize-btn');
  if (!button) return;

  const icon = button.querySelector('i');
  const label = sidebarMaximized
    ? `Restore ${config.sidebar.name}`
    : `Maximize ${config.sidebar.name}`;

  button.title = label;
  button.setAttribute('aria-label', label);
  button.setAttribute('aria-pressed', String(sidebarMaximized));
  button.classList.toggle('active', sidebarMaximized);
  if (icon) {
    icon.className = `fa-solid ${sidebarMaximized ? 'fa-compress' : 'fa-expand'}`;
  }
}

function setSidebarMaximized(nextMaximized) {
  const shouldMaximize = Boolean(nextMaximized);
  if (sidebarMaximized === shouldMaximize) {
    updateSidebarMaximizeButton();
    return;
  }

  sidebarMaximized = shouldMaximize;
  if (sidebarMaximized) {
    // Instructions focus mode is mutually exclusive with a maximized right panel.
    maximizedPanelId = null;
    // Maximizing while hidden shows Instructions first.
    sidebarVisible = true;
  }

  updatePanelVisibility();
}

function toggleSidebarMaximized() {
  setSidebarMaximized(!sidebarMaximized);
}

function ensureSidebarLoaded() {
  const sidebar = document.getElementById('sidebar');
  const loadingEl = sidebar?.querySelector('.panel-loading');
  const iframe = sidebar?.querySelector('iframe');
  const currentSrc = iframe?.getAttribute('src') || '';
  if (loadingEl && iframe && !currentSrc) {
    loadPanelWithRetry(loadingEl);
  }
}

function setSidebarVisible(nextVisible) {
  const shouldShow = Boolean(nextVisible);

  if (!shouldShow) {
    if (visibleRightPanels().length === 0) {
      activeRightPanelId = defaultRightPanelId();
      normalizeRightPanelState();
    }
    if (visibleRightPanels().length === 0) {
      setRightPanelNotice('Keep at least one resource visible before hiding Instructions.');
      return;
    }
    // Hiding exits Instructions focus mode.
    sidebarMaximized = false;
  }

  if (sidebarVisible === shouldShow) {
    updatePanelVisibility();
    return;
  }

  sidebarVisible = shouldShow;
  updatePanelVisibility();

  if (shouldShow) {
    ensureSidebarLoaded();
  } else {
    setRightPanelNotice(`${config.sidebar.name} hidden. Use the tab bar to show it again.`);
  }
}

function updateComponentLayout() {
  const main = document.getElementById('container');
  const sidebar = document.getElementById('sidebar');
  const rightStack = document.getElementById('rightStack');
  const verticalResizer = document.getElementById('verticalResizer');
  const rightPanelCount = visibleRightPanels().length;
  const sidebarOnly = sidebarVisible && (sidebarMaximized || rightPanelCount === 0);

  main?.classList.toggle('sidebar-only', sidebarOnly);
  main?.classList.toggle('sidebar-maximized', sidebarMaximized);
  rightStack?.classList.toggle('empty', sidebarOnly);

  if (sidebar) {
    sidebar.style.display = sidebarVisible ? '' : 'none';
  }

  if (verticalResizer) {
    verticalResizer.style.display = sidebarOnly || !sidebarVisible || rightPanelCount === 0 || maximizedPanelId || sidebarMaximized ? 'none' : '';
  }

  if (sidebar) {
    if (sidebarOnly) {
      sidebar.style.width = '100%';
    } else if (sidebar.style.width === '100%') {
      sidebar.style.width = '';
    }
  }

  updateSidebarMaximizeButton();
}

function renderTerminalTabs(section) {
  const tabbar = section.querySelector('.terminal-tabbar');
  if (!tabbar) return;

  const canAddTab = terminalTabs.length < TERMINAL_MAX_TABS;
  const tabButtons = terminalTabs.map(tab => {
    const isActive = tab.id === activeTerminalTabId;
    const isActiveRestartTab = restartCommandActive && tab.id === restartTerminalTabId;
    const canCloseTab = terminalTabs.length > 1 && !isActiveRestartTab;
    return `
      <div class="terminal-tab${isActive ? ' active' : ''}">
        <button
          type="button"
          class="terminal-tab-button"
          data-terminal-tab="${tab.id}"
          role="tab"
          aria-selected="${isActive}"
          title="${terminalTabLabel(tab.id)}"
        >
          <span class="terminal-tab-shell">${terminalTabLabel(tab.id)}</span>
          <span class="terminal-tab-index">#${tab.id + 1}</span>
        </button>
        <button
          type="button"
          class="terminal-tab-close"
          data-terminal-tab-close="${tab.id}"
          title="${isActiveRestartTab ? 'Restart is running' : `Close ${terminalTabLabel(tab.id)}`}"
          aria-label="${isActiveRestartTab ? 'Restart is running' : `Close ${terminalTabLabel(tab.id)}`}"
          ${canCloseTab ? '' : 'disabled'}
        >
          <i class="fa-solid fa-xmark"></i>
        </button>
      </div>
    `;
  }).join('');

  tabbar.innerHTML = `
    <div class="terminal-tabs">${tabButtons}</div>
    <button
      type="button"
      class="terminal-tab-add"
      title="${canAddTab ? 'New terminal' : 'Terminal limit reached'}"
      aria-label="${canAddTab ? 'New terminal' : 'Terminal limit reached'}"
      ${canAddTab ? '' : 'disabled'}
    >
      <i class="fa-solid fa-plus"></i>
    </button>
  `;

  tabbar.querySelectorAll('.terminal-tab-button').forEach(button => {
    button.addEventListener('click', () => {
      switchTerminalTab(Number(button.dataset.terminalTab));
    });
  });

  tabbar.querySelectorAll('.terminal-tab-close').forEach(button => {
    button.addEventListener('click', (event) => {
      event.stopPropagation();
      closeTerminalTab(Number(button.dataset.terminalTabClose));
    });
  });

  tabbar.querySelector('.terminal-tab-add')?.addEventListener('click', () => addTerminalTab());
}

function renderTerminalFrames(section) {
  if (!section) return;
  const frames = section.querySelector('.terminal-frames');
  if (!frames) return;

  frames.querySelectorAll('.terminal-frame').forEach(frame => {
    const tabId = Number(frame.dataset.terminalFrame);
    if (!terminalTabs.some(tab => tab.id === tabId)) {
      frame.remove();
    }
  });

  terminalTabs.forEach(tab => {
    let frame = frames.querySelector(`.terminal-frame[data-terminal-frame="${tab.id}"]`);
    const isActive = tab.id === activeTerminalTabId;

    if (!frame) {
      frame = document.createElement('div');
      frame.className = 'terminal-frame';
      frame.dataset.terminalFrame = tab.id;
      frame.innerHTML = `
        <div class="panel-loading" data-url="${terminalTabPath(tab.id)}">
          <i class="fa-solid fa-spinner"></i>
          <span>Connecting...</span>
        </div>
        <iframe title="${terminalTabLabel(tab.id)}"></iframe>
      `;
      frames.appendChild(frame);
      if (panelLoadersStarted) {
        loadPanelWithRetry(frame.querySelector('.panel-loading'));
      }
    }

    frame.classList.toggle('active', isActive);
    frame.classList.toggle('hidden', !isActive);
  });
}

function updateTerminalPanelUrl(section, shouldReload = false) {
  if (!section) return;
  const activeTab = getActiveTerminalTab();
  const activeUrl = terminalTabPath(activeTab.id);
  const activeFrame = section.querySelector(`.terminal-frame[data-terminal-frame="${activeTab.id}"]`);
  const loadingEl = activeFrame?.querySelector('.panel-loading');
  const iframe = activeFrame?.querySelector('iframe');
  const openButton = section.querySelector('.open-panel-btn');

  if (openButton) {
    openButton.href = activeUrl;
  }

  if (iframe) {
    iframe.title = terminalTabLabel(activeTab.id);
  }

  if (!loadingEl) return;

  if (shouldReload) {
    loadingEl.dataset.url = activeUrl;
    if (iframe) iframe.src = '';
    loadingEl.classList.remove('hidden');
    loadPanelWithRetry(loadingEl);
  }
}

function setupTerminalPanel(section) {
  renderTerminalTabs(section);
  renderTerminalFrames(section);
  updateTerminalPanelUrl(section);
}

function switchTerminalTab(tabId) {
  if (!terminalTabs.some(tab => tab.id === tabId)) return;

  activeTerminalTabId = tabId;
  const section = document.getElementById(`panel-${TERMINAL_PANEL_ID}`);
  if (!section) return;

  renderTerminalTabs(section);
  renderTerminalFrames(section);
  updateTerminalPanelUrl(section);
}

function addTerminalTab(label = '') {
  const tabId = nextTerminalTabId();
  if (tabId === null) return;

  terminalTabs.push({ id: tabId, label: typeof label === 'string' ? label : '' });
  activeTerminalTabId = tabId;

  const section = document.getElementById(`panel-${TERMINAL_PANEL_ID}`);
  if (!section) return;

  renderTerminalTabs(section);
  renderTerminalFrames(section);
  updateTerminalPanelUrl(section);
}

function closeTerminalTab(tabId) {
  if (terminalTabs.length === 1) return;
  if (restartCommandActive && tabId === restartTerminalTabId) return;

  const tabIndex = terminalTabs.findIndex(tab => tab.id === tabId);
  if (tabIndex === -1) return;

  terminalTabs.splice(tabIndex, 1);
  if (restartTerminalTabId === tabId) {
    restartTerminalTabId = null;
  }

  if (activeTerminalTabId === tabId) {
    const nextTab = terminalTabs[Math.min(tabIndex, terminalTabs.length - 1)];
    activeTerminalTabId = nextTab.id;
  }

  const section = document.getElementById(`panel-${TERMINAL_PANEL_ID}`);
  if (!section) return;

  renderTerminalTabs(section);
  renderTerminalFrames(section);
  updateTerminalPanelUrl(section);
}

function normalizeCodeFileRequest(data) {
  const rawPath = String(data?.path || '').trim().replace(/\\/g, '/').replace(/^\/+/, '');
  const match = rawPath.match(CODE_FILE_PATTERN);
  if (!match) return null;

  const line = Number(data?.line || 0);
  const column = Number(data?.column || 0);
  const explicitTrack = normalizeTrack(data?.track) || normalizeTrack(match[1]);
  const track = explicitTrack || readActiveTrack();
  const workspacePath = match[2];
  const isDirectory = data?.kind === 'directory' || workspacePath.endsWith('/');

  if (explicitTrack) {
    storeActiveTrack(explicitTrack);
  }

  return {
    sourcePath: rawPath,
    workspacePath,
    remotePath: `${codeServerRoot(track)}/${workspacePath}`,
    kind: isDirectory ? 'directory' : 'file',
    track,
    line: !isDirectory && Number.isInteger(line) && line > 0 ? line : null,
    column: !isDirectory && Number.isInteger(column) && column > 0 ? column : null
  };
}

async function openCodeFileWithBridge(fileRequest) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), CODE_OPEN_BRIDGE_TIMEOUT_MS);

  try {
    const response = await fetch(CODE_OPEN_BRIDGE_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        path: fileRequest.workspacePath,
        track: fileRequest.track,
        kind: fileRequest.kind,
        line: fileRequest.line,
        column: fileRequest.column
      }),
      signal: controller.signal
    });

    if (!response.ok) {
      throw new Error(`Code open bridge responded with ${response.status}`);
    }
  } finally {
    window.clearTimeout(timeoutId);
  }
}

function vscodeUrlForFile(fileRequest) {
  if (fileRequest.kind === 'directory') {
    return `/vscode/?folder=${encodeURI(fileRequest.remotePath.replace(/\/+$/, ''))}`;
  }

  const positionSuffix = fileRequest.line
    ? `:${fileRequest.line}${fileRequest.column ? `:${fileRequest.column}` : ''}`
    : '';
  const remoteUri = `vscode-remote://${window.location.host}${encodeURI(fileRequest.remotePath + positionSuffix)}`;
  const payload = [['openFile', remoteUri]];

  if (fileRequest.line) {
    payload.push(['gotoLineMode', 'true']);
  }

  return `${codePanelPath(fileRequest.track)}&payload=${encodeURIComponent(JSON.stringify(payload))}`;
}

function loadPanelUrl(section, url) {
  const loadingEl = section?.querySelector('.panel-loading');
  const iframe = section?.querySelector('iframe');
  const openButton = section?.querySelector('.open-panel-btn');

  if (openButton) {
    openButton.href = url;
  }

  if (!loadingEl || !iframe) return;

  loadingEl.dataset.url = url;
  iframe.src = '';
  loadingEl.classList.remove('hidden');
  loadPanelWithRetry(loadingEl);
}

async function fetchRedisInsightJson(url) {
  const response = await fetch(url, { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`Redis Insight ${url} responded with ${response.status}`);
  }
  return response.json();
}

async function fetchRedisInsightOk(url) {
  const response = await fetch(url, { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`Redis Insight ${url} responded with ${response.status}`);
  }
}

function selectRedisInsightDatabase(databases = []) {
  if (!Array.isArray(databases) || databases.length === 0) {
    throw new Error('Redis Insight has no configured databases yet.');
  }

  return databases.find(database => database.name === REDIS_INSIGHT_DATABASE_NAME)
    || databases.find(database => database.host === 'redis' && Number(database.port) === 6379)
    || databases.find(database => Number(database.db) === 0)
    || databases[0];
}

function redisInsightBrowserUrl(database) {
  const id = database?.id;
  if (id === undefined || id === null || id === '') {
    throw new Error('Redis Insight database is missing an id.');
  }
  return `/redisinsight/${encodeURIComponent(id)}/browser`;
}

async function refreshRedisInsightDatabase(database) {
  const id = database?.id;
  if (id === undefined || id === null || id === '') {
    throw new Error('Redis Insight database is missing an id.');
  }

  await fetchRedisInsightOk(`/redisinsight/api/databases/${encodeURIComponent(id)}/connect`);
}

async function resolveRedisInsightBrowserUrl() {
  await fetchRedisInsightJson(REDIS_INSIGHT_HEALTH_URL);
  const databases = await fetchRedisInsightJson(REDIS_INSIGHT_DATABASES_URL);
  const database = selectRedisInsightDatabase(databases);
  await refreshRedisInsightDatabase(database);
  return redisInsightBrowserUrl(database);
}

function loadRedisInsightPanel(loadingEl) {
  const iframe = loadingEl.parentElement.querySelector('iframe');
  const section = loadingEl.closest('.panel');
  const openButton = section?.querySelector('.open-panel-btn');

  const tryLoad = async () => {
    try {
      const url = await resolveRedisInsightBrowserUrl();
      loadingEl.dataset.url = url;
      if (openButton) {
        openButton.href = url;
      }
      iframe.src = url;
      loadingEl.classList.add('hidden');
    } catch (error) {
      console.debug('Waiting for Redis Insight to finish booting.', error);
      setTimeout(tryLoad, REDIS_INSIGHT_READY_RETRY_MS);
    }
  };

  tryLoad();
}

function updateCodePanelUrl(section, shouldReload = false, track = '') {
  if (!section) return;

  const url = codePanelPath(track);
  const loadingEl = section.querySelector('.panel-loading');
  const iframe = section.querySelector('iframe');
  const openButton = section.querySelector('.open-panel-btn');

  if (openButton) {
    openButton.href = url;
  }

  if (!loadingEl) return;

  loadingEl.dataset.url = url;

  if (shouldReload) {
    if (iframe) iframe.src = '';
    loadingEl.classList.remove('hidden');
    loadPanelWithRetry(loadingEl);
  }
}

async function openCodeFileFromDocs(data) {
  const fileRequest = normalizeCodeFileRequest(data);
  if (!fileRequest) return;

  if (maximizedPanelId && maximizedPanelId !== CODE_PANEL_ID) {
    maximizedPanelId = null;
  }

  activateRightPanel(CODE_PANEL_ID, { silent: true });

  const section = document.getElementById(`panel-${CODE_PANEL_ID}`);

  try {
    await openCodeFileWithBridge(fileRequest);
  } catch (error) {
    console.warn('Falling back to code-server payload file open.', error);
    loadPanelUrl(section, vscodeUrlForFile(fileRequest));
  }
}

function openWorkbenchPanelFromDocs(data) {
  const panelId = String(data?.panelId || '').trim();
  if (!panelId) return;

  // Docs links that target Instructions should restore the sidebar if hidden.
  if (panelId === config.sidebar.id || panelId === 'instructions') {
    setSidebarVisible(true);
    return;
  }

  if (!rightPanelById(panelId)) return;

  if (maximizedPanelId && maximizedPanelId !== panelId) {
    maximizedPanelId = null;
  }

  activateRightPanel(panelId, { silent: true });
}

// Try to load a panel, retry until successful
function loadPanelWithRetry(loadingEl) {
  const url = loadingEl.dataset.url;
  const iframe = loadingEl.parentElement.querySelector('iframe');

  if (isRedisInsightUrl(url)) {
    loadRedisInsightPanel(loadingEl);
    return;
  }

  const tryLoad = async () => {
    try {
      const response = await fetch(url, { method: 'HEAD', cache: 'no-store' });
      if (!response.ok && response.status !== 405 && response.type !== 'opaque' && response.type !== 'opaqueredirect') {
        throw new Error(`Panel ${url} responded with ${response.status}`);
      }
      iframe.src = url;
      loadingEl.classList.add('hidden');
    } catch (e) {
      setTimeout(tryLoad, PANEL_READY_RETRY_MS);
    }
  };
  tryLoad();
}

// Start loading all panels
function startPanelLoaders() {
  document.querySelectorAll('.panel-loading').forEach(loadingEl => {
    if (loadingEl.closest('#sidebar') && !sidebarVisible) return;
    loadPanelWithRetry(loadingEl);
  });
  panelLoadersStarted = true;
}

// Toggle sidebar visibility
function toggleSidebarVisibility(visible) {
  setSidebarVisible(visible);
}

function setupSidebarFrameMessages() {
  window.addEventListener('message', (event) => {
    if (event.origin !== window.location.origin) return;

    if (event.data?.type === 'btc-open-code-file') {
      openCodeFileFromDocs(event.data);
      return;
    }

    if (event.data?.type === 'btc-open-workbench-panel') {
      openWorkbenchPanelFromDocs(event.data);
      return;
    }

  });
}

// Toggle panel visibility
function togglePanelVisibility(panelId, visible) {
  if (visible) {
    activateRightPanel(panelId);
  } else {
    hideRightPanel(panelId);
  }
}

// Setup panel header buttons
function setupPanelHeaderButtons() {
  // Refresh buttons
  document.querySelectorAll('.refresh-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const panelId = btn.dataset.panel;
      const section = document.getElementById(`panel-${panelId}`);
      if (panelId === TERMINAL_PANEL_ID) {
        updateTerminalPanelUrl(section, true);
        return;
      }

      if (panelId === CODE_PANEL_ID) {
        updateCodePanelUrl(section, true);
        return;
      }

      const loadingEl = section?.querySelector('.panel-loading');
      const iframe = section?.querySelector('iframe');
      if (iframe && loadingEl) {
        iframe.src = '';
        loadingEl.classList.remove('hidden');
        loadPanelWithRetry(loadingEl);
      }
    });
  });

}

function setRestartButtonBusy(button, busy) {
  const label = button.querySelector('.restart-app-label');
  button.disabled = busy;
  button.setAttribute('aria-busy', String(busy));
  button.title = busy ? 'Restarting App' : 'Restart App';
  button.setAttribute('aria-label', busy ? 'Restarting App' : 'Restart App');
  if (label) {
    label.textContent = busy ? 'Restarting App' : 'Restart App';
  }
}

function setRestartButtonsBusy(busy) {
  document.querySelectorAll('.restart-app-btn').forEach(button => {
    setRestartButtonBusy(button, busy);
  });
}

function rememberRestartTerminalTab(tabId) {
  restartTerminalTabId = tabId;
  const tab = terminalTabs.find(candidate => candidate.id === tabId);
  if (tab) {
    tab.label = 'Restart App';
  }
}

function ensureRestartTerminalTab() {
  if (restartTerminalTabId !== null && terminalTabs.some(tab => tab.id === restartTerminalTabId)) {
    rememberRestartTerminalTab(restartTerminalTabId);
    switchTerminalTab(restartTerminalTabId);
    return restartTerminalTabId;
  }

  const existingRestartTab = terminalTabs.find(tab => tab.label === 'Restart App');
  if (existingRestartTab) {
    rememberRestartTerminalTab(existingRestartTab.id);
    switchTerminalTab(existingRestartTab.id);
    return existingRestartTab.id;
  }

  const nextTabId = nextTerminalTabId();
  if (nextTabId !== null) {
    terminalTabs.push({ id: nextTabId, label: 'Restart App' });
    activeTerminalTabId = nextTabId;
    rememberRestartTerminalTab(nextTabId);
  } else {
    rememberRestartTerminalTab(activeTerminalTabId);
  }

  const section = document.getElementById(`panel-${TERMINAL_PANEL_ID}`);
  if (section) {
    renderTerminalTabs(section);
    renderTerminalFrames(section);
    updateTerminalPanelUrl(section);
  }

  return restartTerminalTabId;
}

function openRestartTerminalTab() {
  if (maximizedPanelId && maximizedPanelId !== TERMINAL_PANEL_ID) {
    maximizedPanelId = null;
  }

  activateRightPanel(TERMINAL_PANEL_ID, { silent: true });

  return ensureRestartTerminalTab();
}

async function runRestartInTerminal(tabId) {
  const response = await fetch(TERMINAL_RESTART_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tabId })
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.error || `Terminal restart command failed with status ${response.status}`);
  }
}

async function readRestartStatus() {
  const response = await fetch(`${TERMINAL_RESTART_ENDPOINT}/status`, {
    headers: { Accept: 'application/json' }
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.error || `Restart status failed with status ${response.status}`);
  }
  return Boolean(body.active);
}

function stopRestartStatusPolling() {
  window.clearTimeout(restartStatusPollTimer);
  restartStatusPollTimer = null;
}

function finishRestartActiveState() {
  restartCommandActive = false;
  stopRestartStatusPolling();
  setRestartButtonsBusy(false);
  const section = document.getElementById(`panel-${TERMINAL_PANEL_ID}`);
  if (section) renderTerminalTabs(section);
}

async function waitForRestartToFinish() {
  stopRestartStatusPolling();

  return new Promise(resolve => {
    const poll = async () => {
      try {
        if (!(await readRestartStatus())) {
          resolve();
          return;
        }
      } catch (_error) {
        // Keep the button protected if the status endpoint briefly reloads with Vite.
      }
      restartStatusPollTimer = window.setTimeout(poll, RESTART_STATUS_POLL_MS);
    };

    restartStatusPollTimer = window.setTimeout(poll, RESTART_STATUS_POLL_MS);
  });
}

async function syncRestartStatusFromServer() {
  try {
    restartCommandActive = await readRestartStatus();
    setRestartButtonsBusy(restartCommandActive);
    if (restartCommandActive) {
      await waitForRestartToFinish();
      finishRestartActiveState();
    }
  } catch (_error) {
    // The bridge can be unavailable while Vite is reconnecting; user clicks will retry.
  }
}

async function restartAppPanel(button) {
  if (restartCommandActive || button.disabled) {
    openRestartTerminalTab();
    return;
  }

  restartCommandActive = true;
  setRestartButtonsBusy(true);
  try {
    const tabId = openRestartTerminalTab();
    await runRestartInTerminal(tabId);
    await waitForRestartToFinish();
  } catch (error) {
    window.alert(error.message || 'Could not restart App.');
  } finally {
    finishRestartActiveState();
  }
}

// Disable iframe pointer events during resize
function disableIframePointerEvents() {
  isResizingPanels = true;
  window.clearTimeout(iframePointerRestoreTimer);

  document.querySelectorAll('iframe').forEach(iframe => {
    iframe.style.pointerEvents = 'none';
  });

  iframePointerRestoreTimer = window.setTimeout(enableIframePointerEvents, IFRAME_POINTER_RESTORE_MS);
}

function enableIframePointerEvents() {
  isResizingPanels = false;
  window.clearTimeout(iframePointerRestoreTimer);
  iframePointerRestoreTimer = null;

  document.querySelectorAll('iframe').forEach(iframe => {
    iframe.style.pointerEvents = '';
  });
}

function focusPanelIframe(panel) {
  const iframe = panel?.querySelector('iframe');
  if (!iframe || iframe.offsetParent === null) return;

  const focusIframeScroller = () => {
    try {
      iframe.focus();
      iframe.contentWindow?.focus();
      const scrollTarget = iframe.contentDocument?.querySelector('.content');
      if (scrollTarget && typeof scrollTarget.focus === 'function') {
        scrollTarget.setAttribute('tabindex', '-1');
        scrollTarget.focus({ preventScroll: true });
      }
    } catch (_error) {
      // Cross-origin frames can reject focus; restoring pointer events is enough there.
    }
  };

  window.requestAnimationFrame(focusIframeScroller);
  window.setTimeout(focusIframeScroller, 150);
}

function setupIframePointerRecovery() {
  window.addEventListener('mouseup', () => {
    if (isResizingPanels) {
      enableIframePointerEvents();
    }
  }, true);

  window.addEventListener('blur', enableIframePointerEvents);

  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
      enableIframePointerEvents();
    }
  });
}

// Setup vertical resizer (sidebar)
function setupResizers() {
  const main = document.getElementById('container');
  const sidebar = document.getElementById('sidebar');

  const verticalResizer = document.getElementById('verticalResizer');
  if (verticalResizer) {
    const handle = verticalResizer.querySelector('.resizer-handle');
    if (handle) {
      // Remove old listeners by cloning
      const newHandle = handle.cloneNode(true);
      handle.parentNode.replaceChild(newHandle, handle);

      newHandle.addEventListener('mousedown', (e) => {
        e.preventDefault();
        disableIframePointerEvents();
        document.body.style.cursor = 'col-resize';

        const onMouseMove = (e) => {
          const mainRect = main.getBoundingClientRect();
          const offsetX = e.clientX - mainRect.left;
          const newWidth = (offsetX / mainRect.width) * 100;
          if (newWidth > 10 && newWidth < 70) {
            sidebar.style.width = newWidth + '%';
          }
        };

        const onMouseUp = () => {
          document.removeEventListener('mousemove', onMouseMove);
          document.removeEventListener('mouseup', onMouseUp);
          document.body.style.cursor = 'default';
          enableIframePointerEvents();
          focusPanelIframe(sidebar);
        };

        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
      });
    }
  }

  // Setup horizontal resizers for initial state
  setupHorizontalResizers();
}

// Setup horizontal resizers (between panels in right stack)
function setupHorizontalResizers() {
  document.querySelectorAll('.right-stack .resizer-horizontal').forEach(resizer => {
    const handle = resizer.querySelector('.resizer-handle');
    if (handle) {
      // Remove old listeners by cloning
      const newHandle = handle.cloneNode(true);
      handle.parentNode.replaceChild(newHandle, handle);

      newHandle.addEventListener('mousedown', (e) => {
        e.preventDefault();
        disableIframePointerEvents();
        document.body.style.cursor = 'row-resize';

        const aboveId = resizer.dataset.above;
        const belowId = resizer.dataset.below;
        const abovePanel = document.getElementById(`panel-${aboveId}`);
        const belowPanel = document.getElementById(`panel-${belowId}`);

        if (!abovePanel || !belowPanel) return;

        // Get initial sizes
        const aboveRect = abovePanel.getBoundingClientRect();
        const belowRect = belowPanel.getBoundingClientRect();
        const combinedHeight = aboveRect.height + belowRect.height;
        const startY = e.clientY;
        const startAboveHeight = aboveRect.height;

        const onMouseMove = (e) => {
          const deltaY = e.clientY - startY;
          const newAboveHeight = startAboveHeight + deltaY;
          const newBelowHeight = combinedHeight - newAboveHeight;

          // Minimum height of 50px for each panel
          if (newAboveHeight > 50 && newBelowHeight > 50) {
            abovePanel.style.flex = 'none';
            belowPanel.style.flex = 'none';
            abovePanel.style.height = newAboveHeight + 'px';
            belowPanel.style.height = newBelowHeight + 'px';
          }
        };

        const onMouseUp = () => {
          document.removeEventListener('mousemove', onMouseMove);
          document.removeEventListener('mouseup', onMouseUp);
          document.body.style.cursor = 'default';
          enableIframePointerEvents();
        };

        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
      });
    }
  });
}

// Initialize when DOM is ready
init();
