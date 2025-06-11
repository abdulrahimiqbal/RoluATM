import { QueryClient, QueryFunction } from "@tanstack/react-query";

// Configure API base URL - support for local and Vercel backend testing
const getApiBaseUrl = () => {
  // Check if there's a URL parameter for the backend URL (for testing)
  const urlParams = new URLSearchParams(window.location.search);
  const backendParam = urlParams.get('backend');
  
  if (backendParam) {
    // Allow connecting to local backend for testing - use Mac's network IP
    if (backendParam === 'local') {
      return 'http://192.168.0.158:8000';
    }
    // Allow connecting to Vercel backend for testing
    if (backendParam === 'vercel') {
      // Use the deployed backend URL - this should match your Vercel deployment
      return 'https://rolu-atm-backend.vercel.app';
    }
    return backendParam;
  }
  
  // Check if running locally (for development)
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://localhost:8000';
  }
  
  // For deployed version, use relative URLs (same domain)
  return '';
};

const API_BASE_URL = getApiBaseUrl();

async function throwIfResNotOk(res: Response) {
  if (!res.ok) {
    const text = (await res.text()) || res.statusText;
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
}

// Helper function to make API requests
export async function apiRequest(path: string, options: RequestInit = {}) {
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
