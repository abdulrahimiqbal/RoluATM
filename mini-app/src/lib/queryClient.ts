import { QueryClient, QueryFunction } from "@tanstack/react-query";

// Configure API base URL - support for local and Vercel backend testing
const getApiBaseUrl = () => {
  // Check if there's a URL parameter for the backend URL (for testing)
  const urlParams = new URLSearchParams(window.location.search);
  const backendParam = urlParams.get('backend');
  
  if (backendParam) {
    // Allow connecting to local backend for testing
    if (backendParam === 'local') {
      // Use HTTPS if the mini app is served over HTTPS to avoid mixed content
      if (window.location.protocol === 'https:') {
        console.warn('⚠️ Cannot connect to HTTP backend from HTTPS page. Using mock mode.');
        return null; // This will trigger mock mode
      }
      return 'http://localhost:8000';
    }
    // Allow connecting to Vercel backend for testing
    if (backendParam === 'vercel') {
      // Use the deployed backend URL - this should match your Vercel deployment
      return 'https://server-k36bxwifq-abdulrahimiqbals-projects.vercel.app';
    }
    return backendParam;
  }
  
  // Default behavior based on environment
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    // Local development - use local backend
    return 'http://localhost:8000';
  }
  
  // Production/Vercel - use deployed backend
  return 'https://server-k36bxwifq-abdulrahimiqbals-projects.vercel.app';
};

const API_BASE_URL = getApiBaseUrl();

// Mock mode detection
const isMockMode = () => {
  return API_BASE_URL === null || (
    window.location.protocol === 'https:' && 
    API_BASE_URL?.startsWith('http:')
  );
};

async function throwIfResNotOk(res: Response) {
  if (!res.ok) {
    const text = (await res.text()) || res.statusText;
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
}

// Mock data for development
const mockTransactionData = {
  id: 'mock-transaction-123',
  amount: 5,
  quarters: 20,
  total: 5.00,
  status: 'pending' as const,
  created_at: new Date().toISOString(),
  expires_at: new Date(Date.now() + 15 * 60 * 1000).toISOString() // 15 minutes from now
};

// Helper function to make API requests
export async function apiRequest(path: string, options: RequestInit = {}) {
  // Handle mock mode
  if (isMockMode()) {
    console.log('🔧 Mock API request:', path, options);
    
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Mock responses based on path
    if (path.includes('/api/transaction/') && !path.includes('/pay')) {
      return mockTransactionData;
    }
    
    if (path.includes('/api/transaction/pay')) {
      return { 
        success: true, 
        message: 'Mock payment processed',
        transaction: { ...mockTransactionData, status: 'complete' }
      };
    }
    
    if (path.includes('/api/transaction/create')) {
      return mockTransactionData;
    }
    
    // Default mock response
    return { success: true, message: 'Mock response' };
  }

  const url = API_BASE_URL ? `${API_BASE_URL}${path}` : path;
  
  // Don't include credentials when connecting to different domains
  const fetchOptions: RequestInit = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };
  
  // Only include credentials for same-origin requests
  if (!API_BASE_URL || API_BASE_URL.includes(window.location.hostname)) {
    fetchOptions.credentials = 'include';
  }

  const res = await fetch(url, fetchOptions);
  await throwIfResNotOk(res);
  return res.json();
}

// Query function for React Query
export const getQueryFn: QueryFunction = async ({ queryKey }) => {
  const [path] = queryKey as [string];
  return apiRequest(path);
};

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      queryFn: getQueryFn,
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 3,
    },
  },
});

// Export utility functions for debugging
export { isMockMode, API_BASE_URL };
