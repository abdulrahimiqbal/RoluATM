import { useState, useEffect } from "react";
import { MiniKit } from "@worldcoin/minikit-js";

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

export function useWorldId(): UseWorldIdReturn {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    // Check if MiniKit is available
    const checkMiniKit = () => {
      if (typeof window !== 'undefined' && window.MiniKit) {
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
    if (typeof window !== 'undefined' && window.MiniKit) {
      // Use real MiniKit if available
      try {
        const result = await MiniKit.commandsAsync.verify({
        action: actionId,
        signal,
        verification_level: "orb",
      });
        
        if (result.finalPayload?.status === "success") {
          return {
            proof: result.finalPayload.proof,
            merkle_root: result.finalPayload.merkle_root,
            nullifier_hash: result.finalPayload.nullifier_hash,
            verification_level: result.finalPayload.verification_level,
          };
        } else {
          throw new Error(result.finalPayload?.error_code || "Verification failed");
        }
      } catch (error) {
        console.error("MiniKit verification error:", error);
        throw error;
      }
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

  return { verify, getWalletBalance, isReady };
}
