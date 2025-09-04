/**
 * EBM Integration Plugin for Zoho Books
 * Handles authentication and communication with the EBM backend service
 */

// Configuration
const CONFIG = {
  API_BASE_URL: 'https://7f4dcaa9ece9.ngrok-free.app/api/v1',
  SESSION_STORAGE_KEY: 'ebm_session_id'
};

/**
 * Authentication Manager
 * Handles login, logout, token management, and API requests
 */
class AuthenticationManager {
  constructor() {
    this.user = null;
    this.apiBaseUrl = CONFIG.API_BASE_URL;
    this.token = null;
  }

  /**
   * Initialize session from localStorage
   */
  initializeSession() {
    try {
      const isAuthenticated = localStorage.getItem('ebm_authenticated');
      const token = localStorage.getItem('ebm_token');
      const userStr = localStorage.getItem('ebm_user');

      console.log('🔍 Checking localStorage:');
      console.log('  - isAuthenticated:', isAuthenticated);
      console.log('  - token exists:', !!token);
      console.log('  - user exists:', !!userStr);

      if (isAuthenticated === 'true' && token && userStr) {
        this.token = token;
        this.user = JSON.parse(userStr);

        console.log('✅ Session restored from localStorage:', this.user.username);
        return true;
      } else {
        console.log('❌ No valid session found in localStorage');
      }
    } catch (error) {
      console.error('Session initialization failed:', error);
      this.clearSession();
    }
    return false;
  }

  /**
   * Clear session from localStorage
   */
  clearSession() {
    localStorage.removeItem('ebm_authenticated');
    localStorage.removeItem('ebm_token');
    localStorage.removeItem('ebm_user');

    this.user = null;
    this.token = null;
  }

  async login(username, password) {
    try {
      const response = await this.makeRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          username: username.trim(),
          password: password
        })
      });

      if (response.access_token && response.user) {
        this.token = response.access_token;
        this.user = response.user;

        // Store credentials in localStorage
        localStorage.setItem('ebm_authenticated', 'true');
        localStorage.setItem('ebm_token', this.token);
        localStorage.setItem('ebm_user', JSON.stringify(this.user));

        console.log('✅ Session stored in localStorage');

        // Verify the data was actually stored
        console.log('🔍 Verifying stored data:');
        console.log('  - ebm_authenticated:', localStorage.getItem('ebm_authenticated'));
        console.log('  - ebm_token exists:', !!localStorage.getItem('ebm_token'));
        console.log('  - ebm_user exists:', !!localStorage.getItem('ebm_user'));

        return this.user;
      } else {
        throw new Error('Login failed: No access token received');
      }
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  logout() {
    this.clearSession();
    console.log('🔓 User logged out and session cleared');
  }

  isAuthenticated() {
    const storedAuth = localStorage.getItem('ebm_authenticated');
    return storedAuth === 'true' && !!(this.token && this.user);
  }

  async verifySession() {
    const isAuthenticated = localStorage.getItem('ebm_authenticated');

    if (isAuthenticated !== 'true' || !this.token) {
      console.log('❌ Session verification failed: auth flag or token missing');
      return false;
    }

    try {
      // Skip backend verification for now - just check if we have valid stored data
      console.log('✅ Session appears valid based on localStorage');
      return true;

      // TODO: Uncomment this when backend /auth/verify is working
      /*
      const response = await this.makeRequest('/auth/verify');
      if (response && response.valid) {
        return true;
      }
      */
    } catch (error) {
      console.error('Session verification failed:', error);
      this.clearSession();
    }
    return false;
  }

  /**
   * ZFAPPS.request wrapper
   */
  async makeRequest(endpoint, options = {}) {
    const url = `${this.apiBaseUrl}${endpoint}`;

    // ✅ Only include valid keys for ZFAPPS
    const requestConfig = {
      url: url,
      method: options.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...options.headers
      }
    };

    if (this.token) {
      requestConfig.headers['Authorization'] = `Bearer ${this.token}`;
    }

    if (options.body) {
      requestConfig.body = options.body;
    }

    try {
      console.log('Making ZFAPPS request:', requestConfig);

      const response = await ZFAPPS.request(requestConfig);
      console.log('ZFAPPS response:', response);

      let responseData;
      if (typeof response.body === 'string') {
        try {
          responseData = JSON.parse(response.body);
        } catch {
          responseData = { message: response.body };
        }
      } else {
        responseData = response.body || response;
      }

      if (response.status === 401) {
        this.logout();
        throw new Error('Authentication required - please login again');
      }

      if (response.status && response.status >= 400) {
        const errorMsg = responseData.detail || responseData.message || `HTTP ${response.status}`;
        throw new Error(errorMsg);
      }

      return responseData;
    } catch (error) {
      console.error('ZFAPPS request failed:', error);

      // fallback to fetch
      return this.makeDirectRequest(endpoint, options);
    }
  }

  /**
   * Fallback using fetch
   */
  async makeDirectRequest(endpoint, options = {}) {
    const url = `${this.apiBaseUrl}${endpoint}`;

    const headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...options.headers
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        mode: 'cors',          // ✅ only here
        credentials: 'omit'    // ✅ only here
      });

      // Don't treat 401 as auth error for login endpoint
      if (response.status === 401 && !endpoint.includes('/auth/login')) {
        this.logout();
        throw new Error('Authentication required - please login again');
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Direct fetch failed:', error);
      throw error;
    }
  }

  getCurrentUser() {
    return this.user;
  }
}

/**
 * Business Setup Manager
 */
class BusinessSetupManager {
  constructor(authManager) {
    this.auth = authManager;
    this.zohoOrgData = null;
  }

  async initializeBusinessSetup() {
    try {
      const orgResponse = await ZFAPPS.get('organization');
      this.zohoOrgData = orgResponse.organization;

      console.log('Zoho organization data:', this.zohoOrgData);

      const orgId = this.zohoOrgData.organization_id;

      return {
        zoho_org_id: orgId,
        business_name: this.zohoOrgData.name,
        setup_needed: false
      };
    } catch (error) {
      console.error('Business setup initialization failed:', error);
      throw error;
    }
  }
}

/**
 * Main EBM Plugin
 */
class EBMPlugin {
  constructor() {
    this.auth = new AuthenticationManager();
    this.businessSetup = new BusinessSetupManager(this.auth);
    this.zohoApp = null;
    this.currentInvoice = null;

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.init());
    } else {
      this.init();
    }
  }

  async init() {
    try {
      console.log('🚀 Initializing EBM Plugin...');

      // Show loading state immediately
      this.showLoadingState();

      // First, check for existing session BEFORE showing any UI
      console.log('🔐 Checking for existing session...');
      const restored = this.auth.initializeSession();

      if (restored) {
        console.log('🔐 Session found! Initializing authenticated state...');

        // Initialize Zoho SDK and other services in background
        this.zohoApp = await ZFAPPS.extension.init();
        console.log('✅ Zoho SDK initialized');

        await this.testAPIConnectivity();
        this.setupEventListeners();

        // Show main interface immediately for authenticated users
        await this.showMainInterface();

        // Verify session in background (optional)
        this.auth.verifySession().then(isValid => {
          if (!isValid) {
            console.log('❌ Background verification failed - session may be expired');
            this.showLoginForm();
          }
        }).catch(err => {
          console.log('❌ Background verification error:', err);
        });

        return;
      }

      // No session found - initialize normally and show login
      console.log('❌ No session found - initializing login flow');

      this.zohoApp = await ZFAPPS.extension.init();
      console.log('✅ Zoho SDK initialized');

      await this.testAPIConnectivity();
      this.setupEventListeners();

      console.log('📋 Showing login form');
      this.showLoginForm();

    } catch (error) {
      console.error('Plugin initialization failed:', error);
      this.showError('Failed to initialize plugin: ' + error.message);
    }
  }

  async testAPIConnectivity() {
    try {
      console.log('🔍 Testing API connectivity...');
      const response = await ZFAPPS.request({
        url: `${CONFIG.API_BASE_URL.replace('/api/v1', '')}/health`,
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      console.log('✅ API connectivity test successful:', response);
      return true;
    } catch (error) {
      console.error('❌ API connectivity test failed:', error);
      return false;
    }
  }

  setupEventListeners() {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
      loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await this.handleLogin();
      });
    }

    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => {
        this.handleLogout();
      });
    }
  }

  async handleLogin() {
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const loginBtn = document.getElementById('loginBtn');
    const errorDiv = document.getElementById('login-error');
    const statusDiv = document.getElementById('login-status');

    const username = usernameInput.value.trim();
    const password = passwordInput.value;

    if (!username || !password) {
      this.showError('Please enter both username and password', errorDiv);
      return;
    }

    try {
      loginBtn.disabled = true;
      loginBtn.textContent = 'Logging in...';
      statusDiv.textContent = 'Authenticating...';
      statusDiv.className = 'status loading';
      errorDiv.classList.add('hidden');

      const user = await this.auth.login(username, password);
      console.log('✅ Login successful:', user);

      statusDiv.textContent = 'Login successful! Initializing...';
      statusDiv.className = 'status success';

      setTimeout(async () => {
        await this.showMainInterface();
      }, 1000);
    } catch (error) {
      console.error('Login failed:', error);
      this.showError(error.message, errorDiv);
    } finally {
      loginBtn.disabled = false;
      loginBtn.textContent = 'Login';
    }
  }

  handleLogout() {
    this.auth.logout();
    this.showLoginForm();
    console.log('🔓 User logged out');
  }

  showLoadingState() {
    document.getElementById('loading-container').classList.remove('hidden');
    document.getElementById('login-container').classList.add('hidden');
    document.getElementById('main-container').classList.add('hidden');
    this.resizeWidget(350, 150);
  }

  showLoginForm() {
    document.getElementById('loading-container').classList.add('hidden');
    document.getElementById('login-container').classList.remove('hidden');
    document.getElementById('main-container').classList.add('hidden');
    this.resizeWidget(350, 300);
  }

  async showMainInterface() {
    try {
      document.getElementById('loading-container').classList.add('hidden');
      document.getElementById('login-container').classList.add('hidden');
      document.getElementById('main-container').classList.remove('hidden');

      const user = this.auth.getCurrentUser();
      document.getElementById('current-username').textContent = user.username;
      document.getElementById('user-role').textContent = `Role: ${user.role}`;

      await this.initializeBusinessIntegration();
      await this.loadCurrentInvoice();
      this.resizeWidget(400, 500);
    } catch (error) {
      console.error('Failed to show main interface:', error);
      this.showError('Failed to initialize main interface: ' + error.message);
    }
  }

  async initializeBusinessIntegration() {
    const statusDiv = document.getElementById('ebm-status');
    try {
      statusDiv.innerHTML = '<div class="status loading">Connecting...</div>';
      const businessData = await this.businessSetup.initializeBusinessSetup();
      statusDiv.innerHTML = `<div class="status success">✅ Connected to: ${businessData.business_name}</div>`;
    } catch (error) {
      console.error('Business integration failed:', error);
      statusDiv.innerHTML = `<div class="error">❌ Failed: ${error.message}</div>`;
    }
  }

  async loadCurrentInvoice() {
    const invoiceDiv = document.getElementById('invoice-info');
    try {
      const invoiceResponse = await ZFAPPS.get('invoice');
      this.currentInvoice = invoiceResponse.invoice;
      if (this.currentInvoice && this.currentInvoice.invoice_id) {
        invoiceDiv.innerHTML = `
          <div class="success">
            📋 Invoice #${this.currentInvoice.invoice_number}<br>
            <small>Amount: ${this.currentInvoice.currency_code} ${this.currentInvoice.total}</small>
          </div>`;
      } else {
        invoiceDiv.innerHTML = '<div class="status">No invoice selected</div>';
      }
    } catch (error) {
      console.error('Failed to load invoice:', error);
      invoiceDiv.innerHTML = `<div class="error">❌ Failed: ${error.message}</div>`;
    }
  }

  resizeWidget(width, height) {
    try {
      ZFAPPS.invoke('RESIZE', { width: `${width}px`, height: `${height}px` });
    } catch (error) {
      console.error('Failed to resize widget:', error);
    }
  }

  showError(message, container = null) {
    // Hide loading state when showing errors
    document.getElementById('loading-container').classList.add('hidden');

    if (container) {
      container.textContent = message;
      container.classList.remove('hidden');
    } else {
      alert('Error: ' + message);
      this.showLoginForm(); // Fallback to login form on general errors
    }
  }
}

// Debug functions for testing localStorage
window.debugLocalStorage = function() {
  console.log('🔍 localStorage Debug:');
  console.log('  - ebm_authenticated:', localStorage.getItem('ebm_authenticated'));
  console.log('  - ebm_token:', localStorage.getItem('ebm_token'));
  console.log('  - ebm_user:', localStorage.getItem('ebm_user'));

  alert(`localStorage Debug:
ebm_authenticated: ${localStorage.getItem('ebm_authenticated')}
ebm_token: ${localStorage.getItem('ebm_token') ? 'EXISTS' : 'NULL'}
ebm_user: ${localStorage.getItem('ebm_user') ? 'EXISTS' : 'NULL'}`);
};

window.testSetStorage = function() {
  localStorage.setItem('ebm_test', 'test_value');
  const testValue = localStorage.getItem('ebm_test');
  console.log('🧪 Test storage result:', testValue);
  alert(`Test storage result: ${testValue}`);
};

window.clearStorage = function() {
  localStorage.removeItem('ebm_authenticated');
  localStorage.removeItem('ebm_token');
  localStorage.removeItem('ebm_user');
  localStorage.removeItem('ebm_test');
  console.log('🗑️ Storage cleared');
  alert('Storage cleared! Please refresh the page.');
};

// Initialize the plugin
console.log('📦 EBM Plugin script loaded');
new EBMPlugin();

