/**
 * ChronoRift API Client
 * Handles HTTP requests and WebSocket connections to backend server
 * Provides authentication, error handling, and real-time communication
 */

export class APIClient {
  constructor(options = {}) {
    this.baseURL = options.baseURL || 'http://localhost:8000/api';
    this.wsURL = options.wsURL || 'ws://localhost:8000/ws';
    this.timeout = options.timeout || 10000;
    this.token = localStorage.getItem('authToken') || null;
    this.userId = localStorage.getItem('userId') || null;

    this.ws = null;
    this.wsReconnectAttempts = 0;
    this.wsMaxReconnectAttempts = 5;
    this.wsReconnectDelay = 3000;
    this.wsListeners = {};
    this.wsConnecting = false;
  }

  /**
   * Make HTTP request
   */
  async request(method, endpoint, data = null, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // Add auth token if available
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const config = {
        method,
        headers,
        signal: AbortSignal.timeout(this.timeout),
      };

      if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
        config.body = JSON.stringify(data);
      }

      const response = await fetch(url, config);

      // Handle 401 - Token expired
      if (response.status === 401) {
        this.clearAuth();
        throw new Error('Authentication expired. Please log in again.');
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error [${method} ${endpoint}]:`, error.message);
      throw error;
    }
  }

  /**
   * GET request
   */
  get(endpoint, options = {}) {
    return this.request('GET', endpoint, null, options);
  }

  /**
   * POST request
   */
  post(endpoint, data = {}, options = {}) {
    return this.request('POST', endpoint, data, options);
  }

  /**
   * PUT request
   */
  put(endpoint, data = {}, options = {}) {
    return this.request('PUT', endpoint, data, options);
  }

  /**
   * PATCH request
   */
  patch(endpoint, data = {}, options = {}) {
    return this.request('PATCH', endpoint, data, options);
  }

  /**
   * DELETE request
   */
  delete(endpoint, options = {}) {
    return this.request('DELETE', endpoint, null, options);
  }

  /**
   * Authentication - Register
   */
  async register(username, email, password) {
    try {
      const response = await this.post('/auth/register', {
        username,
        email,
        password,
      });

      this.setAuth(response.token, response.userId);
      return response;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Authentication - Login
   */
  async login(email, password) {
    try {
      const response = await this.post('/auth/login', {
        email,
        password,
      });

      this.setAuth(response.token, response.userId);
      return response;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Authentication - Logout
   */
  async logout() {
    try {
      await this.post('/auth/logout');
      this.clearAuth();
    } catch (error) {
      // Clear auth even if request fails
      this.clearAuth();
    }
  }

  /**
   * Set authentication token
   */
  setAuth(token, userId) {
    this.token = token;
    this.userId = userId;
    localStorage.setItem('authToken', token);
    localStorage.setItem('userId', userId);
  }

  /**
   * Clear authentication
   */
  clearAuth() {
    this.token = null;
    this.userId = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('userId');
    if (this.ws) {
      this.disconnect();
    }
  }

  /**
   * Get current player data
   */
  async getPlayer() {
    return this.get('/player');
  }

  /**
   * Update player profile
   */
  async updatePlayer(data) {
    return this.put('/player', data);
  }

  /**
   * Get player team
   */
  async getTeam() {
    return this.get('/player/team');
  }

  /**
   * Add Echo to team
   */
  async addToTeam(echoId) {
    return this.post('/player/team', { echoId });
  }

  /**
   * Remove Echo from team
   */
  async removeFromTeam(echoId) {
    return this.delete(`/player/team/${echoId}`);
  }

  /**
   * Get player inventory
   */
  async getInventory() {
    return this.get('/player/inventory');
  }

  /**
   * Get all available Echoes
   */
  async getEchoes(filters = {}) {
    const params = new URLSearchParams(filters).toString();
    const endpoint = params ? `/echoes?${params}` : '/echoes';
    return this.get(endpoint);
  }

  /**
   * Get Echo by ID
   */
  async getEcho(echoId) {
    return this.get(`/echoes/${echoId}`);
  }

  /**
   * Get leaderboard
   */
  async getLeaderboard(options = {}) {
    const { limit = 50, offset = 0, type = 'global' } = options;
    return this.get(
      `/leaderboard?type=${type}&limit=${limit}&offset=${offset}`
    );
  }

  /**
   * Get world zones
   */
  async getZones() {
    return this.get('/world/zones');
  }

  /**
   * Get zone details
   */
  async getZone(zoneId) {
    return this.get(`/world/zones/${zoneId}`);
  }

  /**
   * Get world anomalies
   */
  async getAnomalies() {
    return this.get('/world/anomalies');
  }

  /**
   * Start battle
   */
  async startBattle(battleData) {
    return this.post('/battles', battleData);
  }

  /**
   * Submit battle action
   */
  async submitBattleAction(battleId, action) {
    return this.post(`/battles/${battleId}/action`, action);
  }

  /**
   * Get battle results
   */
  async getBattleResults(battleId) {
    return this.get(`/battles/${battleId}/results`);
  }

  /**
   * Connect WebSocket
   */
  connect() {
    if (this.wsConnecting || this.ws) return Promise.resolve();

    this.wsConnecting = true;

    return new Promise((resolve, reject) => {
      try {
        const url = `${this.wsURL}?token=${this.token}&userId=${this.userId}`;
        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.wsConnecting = false;
          this.wsReconnectAttempts = 0;
          this.emit('connected');
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.wsConnecting = false;
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.ws = null;
          this.wsConnecting = false;
          this.emit('disconnected');
          this.attemptReconnect();
        };
      } catch (error) {
        this.wsConnecting = false;
        reject(error);
      }
    });
  }

  /**
   * Attempt WebSocket reconnection
   */
  attemptReconnect() {
    if (this.wsReconnectAttempts >= this.wsMaxReconnectAttempts) {
      console.error(
        'WebSocket: Max reconnection attempts reached'
      );
      return;
    }

    this.wsReconnectAttempts++;
    const delay = this.wsReconnectDelay * Math.pow(2, this.wsReconnectAttempts - 1);

    console.log(
      `WebSocket: Reconnecting in ${delay}ms (attempt ${this.wsReconnectAttempts}/${this.wsMaxReconnectAttempts})`
    );

    setTimeout(() => {
      this.connect().catch((error) => {
        console.error('Reconnection failed:', error);
      });
    }, delay);
  }

  /**
   * Disconnect WebSocket
   */
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Send WebSocket message
   */
  send(type, data = {}) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket not connected');
      return false;
    }

    try {
      this.ws.send(
        JSON.stringify({
          type,
          data,
          timestamp: Date.now(),
        })
      );
      return true;
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
      return false;
    }
  }

  /**
   * Handle incoming WebSocket message
   */
  handleMessage(message) {
    const { type, data } = message;

    // Emit to listeners
    if (this.wsListeners[type]) {
      this.wsListeners[type].forEach((callback) => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in WebSocket listener (${type}):`, error);
        }
      });
    }

    // System events
    this.emit(type, data);
  }

  /**
   * Register WebSocket listener
   */
  on(type, callback) {
    if (!this.wsListeners[type]) {
      this.wsListeners[type] = [];
    }
    this.wsListeners[type].push(callback);
  }

  /**
   * Unregister WebSocket listener
   */
  off(type, callback) {
    if (!this.wsListeners[type]) return;
    this.wsListeners[type] = this.wsListeners[type].filter(
      (cb) => cb !== callback
    );
  }

  /**
   * Emit local event
   */
  emit(type, data) {
    if (this.wsListeners[type]) {
      this.wsListeners[type].forEach((callback) => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in event listener (${type}):`, error);
        }
      });
    }
  }

  /**
   * Subscribe to battle updates
   */
  subscribeToBattle(battleId) {
    return this.send('subscribe:battle', { battleId });
  }

  /**
   * Subscribe to player updates
   */
  subscribeToPlayer() {
    return this.send('subscribe:player');
  }

  /**
   * Subscribe to world events
   */
  subscribeToWorld() {
    return this.send('subscribe:world');
  }

  /**
   * Get connection status
   */
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Check if authenticated
   */
  isAuthenticated() {
    return !!this.token;
  }
}

/**
 * Global API client instance
 */
let apiClientInstance = null;

export function initializeAPIClient(options = {}) {
  apiClientInstance = new APIClient(options);
  return apiClientInstance;
}

export function getAPIClient() {
  if (!apiClientInstance) {
    apiClientInstance = new APIClient();
  }
  return apiClientInstance;
}

export default APIClient;
