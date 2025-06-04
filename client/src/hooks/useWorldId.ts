import { useState, useEffect } from "react";

interface WorldIDProof {
  proof: string;
  merkle_root: string;
  nullifier_hash: string;
  verification_level: string;
}

interface UseWorldIdReturn {
  verify: (actionId: string, signal: string) => Promise<WorldIDProof>;
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
        if (process.env.NODE_ENV === "development") {
          setIsReady(true);
        }
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
              proof: `mock_proof_${Date.now()}`,
              merkle_root: `mock_merkle_root_${Date.now()}`,
              nullifier_hash: `mock_nullifier_${Date.now()}`,
              verification_level: "orb",
            });
          } else {
            reject(new Error("Verification cancelled"));
          }
        }, 2000); // Simulate 2 second verification time
      });
    }
  };

  return { verify, isReady };
}
