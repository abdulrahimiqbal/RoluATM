import { useEffect, useState } from 'react';
import { MiniKit } from '@worldcoin/minikit-js';

interface WorldIdProof {
  proof: string;
  nullifier_hash: string;
  merkle_root: string;
}

interface WalletBalance {
  usd: number;
  crypto: number;
  symbol: string;
}

interface UseWorldIdReturn {
  verify: (signal: string, action: string) => Promise<WorldIdProof>;
  getWalletBalance: () => Promise<WalletBalance>;
  isReady: boolean;
  isDevelopment: boolean;
}

// Development mode detection
const isDevelopmentMode = () => {
  return !MiniKit.isInstalled() && (
    window.location.hostname === 'localhost' || 
    window.location.hostname === '127.0.0.1' ||
    window.location.hostname.includes('vercel.app')
  );
};

export function useWorldId(): UseWorldIdReturn {
  const [isReady, setIsReady] = useState(false);
  const isDevelopment = isDevelopmentMode();

  useEffect(() => {
    if (isDevelopment) {
      // In development mode, consider it ready immediately
      setIsReady(true);
      console.log('🔧 Development mode: MiniKit functionality will be mocked');
    } else if (MiniKit.isInstalled()) {
      setIsReady(true);
    } else {
      // Listen for MiniKit installation
      const checkMiniKit = () => {
        if (MiniKit.isInstalled()) {
          setIsReady(true);
        }
      };
      
      const interval = setInterval(checkMiniKit, 100);
      
      return () => clearInterval(interval);
    }
  }, [isDevelopment]);

  const verify = async (signal: string, action: string): Promise<WorldIdProof> => {
    try {
      if (isDevelopment) {
        // Mock verification for development
        console.log('🔧 Mock World ID verification:', { signal, action });
        await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate delay
        
        return {
          proof: 'mock_proof_' + Math.random().toString(36).substring(7),
          nullifier_hash: 'mock_nullifier_' + Math.random().toString(36).substring(7),
          merkle_root: 'mock_merkle_' + Math.random().toString(36).substring(7)
        };
      }

      if (!MiniKit.isInstalled()) {
        throw new Error('World App not detected');
      }

      const result = await MiniKit.commands.verify({
        action,
        signal,
        verification_level: 'orb' // or 'device' for device verification
      });

      if (result.status === 'error') {
        throw new Error(result.errorMessage || 'Verification failed');
      }

      return {
        proof: result.proof,
        nullifier_hash: result.nullifier_hash,
        merkle_root: result.merkle_root
      };
    } catch (error: any) {
      throw new Error(error.message || 'World ID verification failed');
    }
  };

  const getWalletBalance = async (): Promise<WalletBalance> => {
    if (isDevelopment) {
      // Mock wallet balance for development
      console.log('🔧 Mock wallet balance');
      return {
        usd: 125.50,
        crypto: 52.42,
        symbol: "WLD"
      };
    }

    if (typeof window !== 'undefined' && window.MiniKit) {
      try {
        // Authenticate wallet connection first
        const walletAuthResult = await MiniKit.commandsAsync.walletAuth();
        
        if (walletAuthResult.finalPayload?.status !== "success") {
          throw new Error("Wallet authentication failed");
        }

        // Get current prices from World's API
        const pricesResponse = await fetch(
          'https://app-backend.worldcoin.dev/public/v1/miniapps/prices?cryptoCurrencies=WLD,USDCE&fiatCurrencies=USD'
        );
        
        if (!pricesResponse.ok) {
          throw new Error("Failed to fetch current prices");
        }
        
        const pricesData = await pricesResponse.json();
        const wldPriceUSD = parseFloat(pricesData.result.prices.WLD.USD.amount) / Math.pow(10, pricesData.result.prices.WLD.USD.decimals);
        
        // For now, return mock balance data based on real price
        // In a real implementation, you would get user's actual token balance
        const cryptoAmount = 1.5; // Mock WLD balance
        const usdAmount = cryptoAmount * wldPriceUSD;
        
        return {
          usd: parseFloat(usdAmount.toFixed(2)),
          crypto: parseFloat(cryptoAmount.toFixed(4)),
          symbol: "WLD"
        };
      } catch (error) {
        console.error("MiniKit wallet error:", error);
        throw new Error("Failed to fetch wallet balance from MiniKit");
      }
    } else {
      // Development fallback
      return {
        usd: 125.50,
        crypto: 52.42,
        symbol: "WLD"
      };
    }
  };

  return {
    isReady,
    verify,
    getWalletBalance,
    isDevelopment
  };
}
