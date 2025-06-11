import { QueryClient, QueryFunction } from "@tanstack/react-query";

// Configure API base URL - support for local and deployed backend
const getApiBaseUrl = () => {
  // Check environment variable first (for deployed version)
  const envApiUrl = (import.meta as any).env?.VITE_API_BASE_URL;
  if (envApiUrl) {
    return envApiUrl;
  }
  
  // For local development, default to local backend
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://localhost:8000';
  }
  
  // For deployed version without environment variable, use relative URLs
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
  // Construct full URL with base URL
  const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;
  
  const res = await fetch(fullUrl, {
    method,
    headers: data ? { "Content-Type": "application/json" } : {},
    body: data ? JSON.stringify(data) : undefined,
    // Only include credentials for same-origin requests
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
    // Construct full URL with base URL
    const url = (queryKey[0] as string);
    const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;
    
    const res = await fetch(fullUrl, {
      // Only include credentials for same-origin requests
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
