/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_WORLD_APP_ID: string
  readonly VITE_API_URL: string
  readonly NODE_ENV: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// Declare MiniKit on window object
declare global {
  interface Window {
    MiniKit?: {
      isInstalled: () => boolean;
      commands: {
        verify: (options: any) => Promise<any>;
        walletAuth: () => Promise<any>;
        pay: (options: any) => Promise<any>;
      };
      commandsAsync: {
        verify: (options: any) => Promise<any>;
        walletAuth: () => Promise<any>;
        pay: (options: any) => Promise<any>;
      };
    };
  }
} 