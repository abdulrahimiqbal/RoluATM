/**
 * Enhanced API client for RoluATM Kiosk App
 * Uses cloud-based Vercel API with fallback to local Pi backend
 */

// Configuration
const VERCEL_API_URL = import.meta.env.VITE_VERCEL_API_URL || 'https://rolu-api.vercel.app/api/v2';
const LOCAL_API_URL = import.meta.env.VITE_LOCAL_API_URL || 'http://localhost:8000';
const USE_CLOUD_API = import.meta.env.VITE_USE_CLOUD_API !== 'false';

// Kiosk ID management
const KIOSK_ID_KEY = 'rolu_kiosk_id';

export function getKioskId(): string {
  let kioskId = localStorage.getItem(KIOSK_ID_KEY);
  if (!kioskId) {
    kioskId = crypto.randomUUID();
    localStorage.setItem(KIOSK_ID_KEY, kioskId);
    console.log('Generated new kiosk ID:', kioskId);
  }
  return kioskId;
}

// API client with automatic failover
class RoluAPIClient {
  private kioskId: string;
  private useCloud: boolean;
  private cloudBaseUrl: string;
  private localBaseUrl: string;

  constructor() {
    this.kioskId = getKioskId();
    this.useCloud = USE_CLOUD_API;
    this.cloudBaseUrl = VERCEL_API_URL;
    this.localBaseUrl = LOCAL_API_URL;
  }

  private async makeRequest(
    endpoint: string, 
    options: RequestInit = {},
    useCloud: boolean = this.useCloud
  ): Promise<Response> {
    const baseUrl = useCloud ? this.cloudBaseUrl : this.localBaseUrl;
    const url = `${baseUrl}${endpoint}`;

    const defaultHeaders = {
      'Content-Type': 'application/json',
      'x-kiosk-id': this.kioskId,
    };

    const config: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return response;
    } catch (error) {
      console.error(`API request failed (${useCloud ? 'cloud' : 'local'}):`, error);
      throw error;
    }
  }

  private async makeRequestWithFallback(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<Response> {
    try {
      // Try cloud API first
      if (this.useCloud) {
        return await this.makeRequest(endpoint, options, true);
      } else {
        // Try local API first
        return await this.makeRequest(endpoint, options, false);
      }
    } catch (error) {
      console.warn('Primary API failed, trying fallback...');
      
      try {
        // Fallback to the other API
        return await this.makeRequest(endpoint, options, !this.useCloud);
      } catch (fallbackError) {
        console.error('Both APIs failed:', { primary: error, fallback: fallbackError });
        throw new Error('All API endpoints are unavailable');
      }
    }
  }

  // Transaction methods
  async createTransaction(amount: number): Promise<Transaction> {
    const quarters = Math.ceil(amount / 0.25);
    const total = amount + 0.50; // Add fee

    const response = await this.makeRequestWithFallback('/transaction/create', {
      method: 'POST',
      body: JSON.stringify({ amount, quarters, total }),
    });

    return response.json();
  }

  async getTransaction(transactionId: string): Promise<Transaction> {
    const response = await this.makeRequestWithFallback(`/transaction/${transactionId}`);
    return response.json();
  }

  // Health and status methods
  async getSystemHealth(): Promise<SystemHealth> {
    try {
      const response = await this.makeRequest('/health', {}, this.useCloud);
      return response.json();
    } catch (error) {
      // For health checks, don't fallback - we want to know which system is down
      throw error;
    }
  }

  async getHardwareStatus(): Promise<HardwareStatus> {
    try {
      // Hardware status should come from local Pi
      const response = await this.makeRequest('/status', {}, false);
      return response.json();
    } catch (error) {
      // Return mock status if Pi is unreachable
      return {
        coinDispenser: 'fault',
        network: 'disconnected',
        security: 'inactive'
      };
    }
  }

  // Kiosk management
  async registerKiosk(name?: string, location?: string): Promise<void> {
    try {
      await this.makeRequest('/kiosk/register', {
        method: 'POST',
        body: JSON.stringify({
          kioskId: this.kioskId,
          name: name || `Kiosk-${this.kioskId.slice(0, 8)}`,
          location: location || 'Unknown Location'
        }),
      }, true); // Always use cloud for kiosk registration
    } catch (error) {
      console.warn('Failed to register kiosk:', error);
      // Don't throw - registration is not critical for operation
    }
  }

  // Utility methods
  getKioskId(): string {
    return this.kioskId;
  }

  isUsingCloudAPI(): boolean {
    return this.useCloud;
  }

  switchToCloudAPI(): void {
    this.useCloud = true;
    console.log('Switched to cloud API');
  }

  switchToLocalAPI(): void {
    this.useCloud = false;
    console.log('Switched to local API');
  }
}

// Types
export interface Transaction {
  id: string;
  amount: number;
  quarters: number;
  total: number;
  mini_app_url: string;
  status: 'pending' | 'paid' | 'dispensing' | 'completed' | 'failed' | 'expired';
  created_at: string;
  expires_at: string;
  kiosk_id?: string;
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  backend: 'online' | 'offline';
  database: 'connected' | 'disconnected' | 'error';
  hardware: {
    tflex: 'hardware' | 'mock' | 'error';
  };
  network: 'connected' | 'disconnected';
  timestamp: string;
}

export interface HardwareStatus {
  coinDispenser: 'ready' | 'low' | 'fault';
  network: 'connected' | 'disconnected';
  security: 'active' | 'inactive';
}

export interface CreateTransactionRequest {
  amount: number;
  quarters: number;
  total: number;
}

// Export singleton instance
export const apiClient = new RoluAPIClient();

// Initialize kiosk registration on startup
apiClient.registerKiosk().catch(console.warn); 