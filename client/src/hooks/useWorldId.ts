import { useState, useEffect } from "react";

interface WorldIDProof {
  proof: string;
  merkle_root: string;
  nullifier_hash: string;
  verification_level: string;
}

interface WalletBalance {
  usd: number;
  crypto: number;
  symbol: string;
}

interface UseWorldIdReturn {
  verify: (actionId: string, signal: string) => Promise<WorldIDProof>;
  getWalletBalance: () => Promise<WalletBalance>;
  isReady: boolean;
}

declare global {
  interface Window {
    MiniKit?: {
      verify: (options: {
        action: string;
        signal?: string;
        verification_level?: string;
      }) => Promise<WorldIDProof>;
      walletAuth: () => Promise<{ address: string }>;
      tokenBalance: (tokenAddress: string) => Promise<{ balance: string; symbol: string }>;
      isInstalled: () => boolean;
    };
  }
}

export function useWorldId(): UseWorldIdReturn {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    // Check if MiniKit is available
    const checkMiniKit = () => {
      if (window.MiniKit?.isInstalled()) {
        setIsReady(true);
      } else {
        // For development, simulate MiniKit availability
        setIsReady(true);
      }
    };

    // Check immediately
    checkMiniKit();

    // Check periodically for MiniKit availability
    const interval = setInterval(checkMiniKit, 1000);

    return () => clearInterval(interval);
  }, []);

  const verify = async (actionId: string, signal: string): Promise<WorldIDProof> => {
    if (window.MiniKit?.isInstalled()) {
      // Use real MiniKit if available
      return await window.MiniKit.verify({
        action: actionId,
        signal,
        verification_level: "orb",
      });
    } else {
      // Development fallback - simulate proof generation
      return new Promise((resolve, reject) => {
        const shouldSucceed = Math.random() > 0.1; // 90% success rate for testing
        
        setTimeout(() => {
          if (shouldSucceed) {
            resolve({
              proof: `mock_proof_${actionId}`,
              merkle_root: `mock_merkle_root_${actionId}`,
              nullifier_hash: `mock_nullifier_${actionId}`,
              verification_level: "orb",
            });
          } else {
            reject(new Error("Verification cancelled"));
          }
        }, 2000); // Simulate 2 second verification time
      });
    }
  };

  const getWalletBalance = async (): Promise<WalletBalance> => {
    if (window.MiniKit?.isInstalled()) {
      try {
        // Authenticate wallet connection
        const walletAuth = await window.MiniKit.walletAuth();
        
        // Get WLD token balance (World ID's native token)
        const wldBalance = await window.MiniKit.tokenBalance("0x163f8c2467924be0ae7b5347228cabf260318753");
        
        // Convert balance to numbers and calculate USD value
        const cryptoAmount = parseFloat(wldBalance.balance) / 1e18; // Convert from wei
        const usdAmount = cryptoAmount * 2.1; // Approximate WLD price
        
        return {
          usd: parseFloat(usdAmount.toFixed(2)),
          crypto: parseFloat(cryptoAmount.toFixed(4)),
          symbol: wldBalance.symbol || "WLD"
        };
      } catch (error) {
        console.error("MiniKit wallet error:", error);
        throw new Error("Failed to fetch wallet balance from MiniKit");
      }
    } else {
      throw new Error("World ID MiniKit not available - please install World App");
    }
  };

  return { verify, getWalletBalance, isReady };
}
