import { QueryClient, QueryFunction } from "@tanstack/react-query";

// Configure API base URL - support for local and Vercel backend testing
const getApiBaseUrl = () => {
  // Check if there's a URL parameter for the backend URL (for testing)
  const urlParams = new URLSearchParams(window.location.search);
  const backendParam = urlParams.get('backend');
  
  if (backendParam) {
    // Allow connecting to local backend for testing
    if (backendParam === 'local') {
      return 'http://localhost:8000';
    }
    // Allow connecting to Vercel backend for testing
    if (backendParam === 'vercel') {
      // Use the deployed backend URL - this should match your Vercel deployment
      return 'https://rolu-atm-backend.vercel.app';
    }
    return backendParam;
  }
  
  // Check environment variable (for Vercel deployment)
  const envApiUrl = (import.meta as any).env?.VITE_API_BASE_URL;
  if (envApiUrl) {
    return envApiUrl;
  }
  
  // Default to relative URLs (same domain)
  return '';
};

const API_BASE_URL = getApiBaseUrl();

async function throwIfResNotOk(res: Response) {
  if (!res.ok) {
    const text = (await res.text()) || res.statusText;
    throw new Error(`${res.status}: ${text}`);
  }
}

export async function apiRequest(
  method: string,
  url: string,
  data?: unknown | undefined,
): Promise<Response> {
  const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;
  
  const res = await fetch(fullUrl, {
    method,
    headers: data ? { "Content-Type": "application/json" } : {},
    body: data ? JSON.stringify(data) : undefined,
    // Remove credentials when connecting to different domain
    ...(API_BASE_URL && !API_BASE_URL.includes(window.location.host) ? {} : { credentials: "include" }),
  });

  await throwIfResNotOk(res);
  return res;
}

type UnauthorizedBehavior = "returnNull" | "throw";
export const getQueryFn: <T>(options: {
  on401: UnauthorizedBehavior;
}) => QueryFunction<T> =
  ({ on401: unauthorizedBehavior }) =>
  async ({ queryKey }) => {
    const fullUrl = (queryKey[0] as string).startsWith('http') 
      ? (queryKey[0] as string) 
      : `${API_BASE_URL}${queryKey[0]}`;
    
    const res = await fetch(fullUrl, {
      // Remove credentials when connecting to different domain
      ...(API_BASE_URL && !API_BASE_URL.includes(window.location.host) ? {} : { credentials: "include" }),
    });

    if (unauthorizedBehavior === "returnNull" && res.status === 401) {
      return null;
    }

    await throwIfResNotOk(res);
    return await res.json();
  };

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      queryFn: getQueryFn({ on401: "throw" }),
      refetchInterval: false,
      refetchOnWindowFocus: false,
      staleTime: Infinity,
      retry: false,
    },
    mutations: {
      retry: false,
    },
  },
});
