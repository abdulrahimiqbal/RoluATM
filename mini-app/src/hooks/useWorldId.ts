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
}

export function useWorldId(): UseWorldIdReturn {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    // Check if MiniKit is ready
    if (MiniKit.isInstalled()) {
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
  }, []);

  const verify = async (signal: string, action: string): Promise<WorldIdProof> => {
    try {
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
    getWalletBalance
  };
}
