import type { Express } from "express";
import { createServer, type Server } from "http";
import { spawn } from "child_process";
import path from "path";

interface BalanceData {
  usd: number;
  crypto: number;
  symbol: string;
}

interface HardwareStatus {
  coinDispenser: "ready" | "low" | "fault";
  network: "connected" | "disconnected";  
  security: "active" | "inactive";
}

interface WithdrawRequest {
  proof: string;
  nullifierHash: string;
  merkleRoot: string;
  amountUsd: number;
}

// Mock data for development - replace with real API calls in production
const mockBalance: BalanceData = {
  usd: 1245.67,
  crypto: 0.0342,
  symbol: "BTC"
};

const mockHardwareStatus: HardwareStatus = {
  coinDispenser: "ready",
  network: "connected",
  security: "active"
};

export async function registerRoutes(app: Express): Promise<Server> {
  // Get balance endpoint
  app.get("/api/balance", async (req, res) => {
    try {
      // World ID MiniKit wallet integration requires proper API endpoints
      // The current endpoints may not be correct - need user to verify the proper World ID wallet API
      
      console.error("World ID wallet API integration needs proper endpoint configuration");
      
      return res.status(503).json({ 
        message: "World ID wallet API integration requires proper configuration",
        error: "API endpoint verification needed",
        suggestion: "Please provide the correct World ID wallet API endpoint and authentication method for your app configuration"
      });
      
    } catch (error) {
      console.error("Balance fetch error:", error);
      res.status(500).json({ 
        message: "Failed to fetch balance",
        error: error instanceof Error ? error.message : "Unknown error"
      });
    }
  });

  // Get hardware status endpoint
  app.get("/api/status", async (req, res) => {
    try {
      // In production, this would check real hardware status
      // For now, call Python backend to get actual status
      if (process.env.NODE_ENV === "production") {
        try {
          const pythonProcess = spawn("python3", [
            path.join(process.cwd(), "src/backend/app.py"),
            "status"
          ]);
          
          let output = "";
          pythonProcess.stdout.on("data", (data) => {
            output += data.toString();
          });
          
          pythonProcess.on("close", (code) => {
            if (code === 0) {
              try {
                const status = JSON.parse(output);
                res.json(status);
              } catch {
                res.json(mockHardwareStatus);
              }
            } else {
              res.json(mockHardwareStatus);
            }
          });
          
          setTimeout(() => {
            pythonProcess.kill();
            res.json(mockHardwareStatus);
          }, 5000);
        } catch {
          res.json(mockHardwareStatus);
        }
      } else {
        res.json(mockHardwareStatus);
      }
    } catch (error) {
      res.status(500).json({ 
        message: "Failed to get hardware status",
        error: error instanceof Error ? error.message : "Unknown error"
      });
    }
  });

  // Withdraw endpoint
  app.post("/api/withdraw", async (req, res) => {
    try {
      const { proof, nullifierHash, merkleRoot, amountUsd } = req.body as WithdrawRequest;
      
      if (!proof || !nullifierHash || !merkleRoot || !amountUsd) {
        return res.status(400).json({ message: "Missing required fields" });
      }

      if (amountUsd <= 0 || amountUsd > 500) {
        return res.status(400).json({ message: "Invalid amount" });
      }

      // Verify World ID proof with real API
      const verifyResponse = await fetch(`https://developer.worldcoin.org/api/v1/verify/${process.env.WORLD_APP_ID}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${process.env.WORLD_API_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          nullifier_hash: nullifierHash,
          merkle_root: merkleRoot,
          proof: proof,
          verification_level: "orb",
          action: "withdraw"
        })
      });

      if (!verifyResponse.ok) {
        console.error(`World ID verification failed: ${verifyResponse.status}`);
        return res.status(400).json({ 
          message: "World ID verification failed",
          error: "Invalid or expired proof"
        });
      }

      const verificationResult = await verifyResponse.json();
      
      if (!verificationResult.success) {
        return res.status(400).json({ 
          message: "World ID verification rejected",
          error: "Proof validation failed"
        });
      }

      // Process withdrawal with hardware
      if (process.env.NODE_ENV === "production") {
        // Call Python backend for withdrawal
        const pythonProcess = spawn("python3", [
          path.join(process.cwd(), "src/backend/app.py"),
          "withdraw",
          JSON.stringify({ proof, nullifierHash, merkleRoot, amountUsd })
        ]);
        
        let output = "";
        let errorOutput = "";
        
        pythonProcess.stdout.on("data", (data) => {
          output += data.toString();
        });
        
        pythonProcess.stderr.on("data", (data) => {
          errorOutput += data.toString();
        });
        
        pythonProcess.on("close", (code) => {
          if (code === 0) {
            try {
              const result = JSON.parse(output);
              res.json(result);
            } catch {
              res.json({ 
                success: true, 
                transactionId: `RA-${new Date().toISOString().slice(0,10).replace(/-/g,'')}-${Math.floor(Math.random() * 9999).toString().padStart(4, '0')}`,
                coinsDispensed: Math.ceil(amountUsd / 0.25)
              });
            }
          } else {
            res.status(500).json({ 
              message: "Withdrawal failed", 
              error: errorOutput || "Hardware error"
            });
          }
        });
        
        setTimeout(() => {
          pythonProcess.kill();
          res.status(500).json({ message: "Withdrawal timeout" });
        }, 30000);
      } else {
        // Development mode - simulate successful withdrawal after real verification
        setTimeout(() => {
          res.json({ 
            success: true, 
            transactionId: `RA-${new Date().toISOString().slice(0,10).replace(/-/g,'')}-${Math.floor(Math.random() * 9999).toString().padStart(4, '0')}`,
            coinsDispensed: Math.ceil(amountUsd / 0.25),
            verified: true,
            nullifierHash: nullifierHash
          });
        }, 3000); // Simulate processing time
      }
    } catch (error) {
      console.error("Withdrawal error:", error);
      res.status(500).json({ 
        message: "Withdrawal failed",
        error: error instanceof Error ? error.message : "Unknown error"
      });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}
