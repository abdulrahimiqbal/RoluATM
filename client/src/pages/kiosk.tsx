import { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import { useWorldId } from "@/hooks/useWorldId";
import { QrCode } from "@/components/Qr";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { 
  Coins, 
  Shield, 
  Bolt, 
  UserCheck, 
  Headphones, 
  AlertTriangle,
  Settings,
  Wifi,
  RefreshCw,
  DollarSign,
  Check,
  Clock,
  Info
} from "lucide-react";

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

const PREDEFINED_AMOUNTS = [20, 50, 100, 200];

export default function KioskPage() {
  const [selectedAmount, setSelectedAmount] = useState<number>(0);
  const [customAmount, setCustomAmount] = useState<string>("");
  const [showWorldIdModal, setShowWorldIdModal] = useState(false);
  const [showProcessingModal, setShowProcessingModal] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [currentActionId, setCurrentActionId] = useState<string>("");
  const { toast } = useToast();

  // Update time every second
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Fetch balance data
  const { data: balance, isLoading: balanceLoading, refetch: refetchBalance } = useQuery<BalanceData>({
    queryKey: ["/api/balance"],
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch hardware status
  const { data: hardwareStatus } = useQuery<HardwareStatus>({
    queryKey: ["/api/status"],
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  // World ID integration
  const { verify, isReady } = useWorldId();

  // Withdraw mutation
  const withdrawMutation = useMutation({
    mutationFn: async (data: WithdrawRequest) => {
      const response = await apiRequest("POST", "/api/withdraw", data);
      return response.json();
    },
    onSuccess: () => {
      setShowProcessingModal(false);
      setShowSuccessModal(true);
      queryClient.invalidateQueries({ queryKey: ["/api/balance"] });
    },
    onError: (error) => {
      setShowProcessingModal(false);
      toast({
        title: "Withdrawal Failed",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const handleAmountSelect = (amount: number) => {
    setSelectedAmount(amount);
    setCustomAmount("");
  };

  const handleCustomAmountSelect = () => {
    const amount = parseFloat(customAmount);
    if (amount >= 1 && amount <= 500) {
      setSelectedAmount(amount);
    } else {
      toast({
        title: "Invalid Amount",
        description: "Please enter an amount between $1 and $500",
        variant: "destructive",
      });
    }
  };

  const handleStartWithdraw = async () => {
    if (selectedAmount <= 0) {
      toast({
        title: "Select Amount",
        description: "Please select an amount to withdraw",
        variant: "destructive",
      });
      return;
    }

    if (!balance || selectedAmount > balance.usd) {
      toast({
        title: "Insufficient Balance",
        description: "You don't have enough balance for this withdrawal",
        variant: "destructive",
      });
      return;
    }

    // Generate a stable action ID for this withdrawal session
    const actionId = `atm-demo-${Date.now()}`;
    setCurrentActionId(actionId);
    setShowWorldIdModal(true);
  };

  const handleWorldIdVerify = async () => {
    try {
      const signal = "withdraw";
      
      const proof = await verify(currentActionId, signal);
      
      setShowWorldIdModal(false);
      setShowProcessingModal(true);

      // Submit withdrawal request
      withdrawMutation.mutate({
        proof: proof.proof,
        nullifierHash: proof.nullifier_hash,
        merkleRoot: proof.merkle_root,
        amountUsd: selectedAmount,
      });
    } catch (error) {
      setShowWorldIdModal(false);
      toast({
        title: "Verification Failed",
        description: "World ID verification was cancelled or failed",
        variant: "destructive",
      });
    }
  };

  const handleNewTransaction = () => {
    setShowSuccessModal(false);
    setSelectedAmount(0);
    setCustomAmount("");
    setCurrentActionId("");
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "ready":
      case "connected":
      case "active":
        return "text-green-500";
      case "low":
        return "text-yellow-500";
      case "fault":
      case "disconnected":
      case "inactive":
        return "text-red-500";
      default:
        return "text-gray-500";
    }
  };

  const getStatusDot = (status: string) => {
    switch (status) {
      case "ready":
      case "connected":
      case "active":
        return "bg-green-500";
      case "low":
        return "bg-yellow-500";
      case "fault":
      case "disconnected":
      case "inactive":
        return "bg-red-500";
      default:
        return "bg-gray-500";
    }
  };

  return (
    <div className="h-screen flex flex-col gradient-primary">
      {/* Header Bar */}
      <header className="bg-white shadow-lg px-8 py-4 flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center">
            <Coins className="text-white text-xl" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-neutral-dark">RoluATM</h1>
            <p className="text-sm text-gray-600">Crypto-to-Cash ATM</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-6">
          {/* Hardware Status Indicators */}
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${hardwareStatus ? getStatusDot(hardwareStatus.coinDispenser) : 'bg-gray-500'}`} />
            <span className="text-sm font-medium text-neutral-dark">
              Coins: {hardwareStatus?.coinDispenser === 'ready' ? 'Normal' : 
                     hardwareStatus?.coinDispenser === 'low' ? 'Low' : 'Fault'}
            </span>
          </div>
          
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full status-pulse ${hardwareStatus ? getStatusDot(hardwareStatus.network) : 'bg-gray-500'}`} />
            <span className="text-sm font-medium text-neutral-dark">
              {hardwareStatus?.network === 'connected' ? 'Online' : 'Offline'}
            </span>
          </div>
          
          {/* Time Display */}
          <div className="text-right">
            <div className="text-lg font-semibold text-neutral-dark">
              {currentTime.toLocaleTimeString('en-US', { 
                hour: 'numeric', 
                minute: '2-digit', 
                hour12: true 
              })}
            </div>
            <div className="text-sm text-gray-600">
              {currentTime.toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric', 
                year: 'numeric' 
              })}
            </div>
          </div>
        </div>
      </header>

      {/* Main Interface */}
      <main className="flex-1 flex">
        {/* Left Panel */}
        <div className="w-2/3 p-8 flex flex-col justify-center">
          <div className="bg-white rounded-3xl shadow-2xl p-12 mb-8">
            <div className="text-center mb-8">
              <h2 className="text-4xl font-bold text-neutral-dark mb-4">Welcome to RoluATM</h2>
              <p className="text-xl text-gray-600">Convert your crypto to cash instantly</p>
            </div>
            
            {/* Balance Display */}
            <div className="gradient-primary rounded-2xl p-8 text-white text-center mb-8">
              <div className="mb-4">
                <span className="text-lg opacity-90">Available Balance</span>
              </div>
              {balanceLoading ? (
                <div className="text-6xl font-bold mb-2">Loading...</div>
              ) : balance ? (
                <>
                  <div className="text-6xl font-bold mb-2">${balance.usd.toFixed(2)}</div>
                  <div className="text-lg opacity-90">{balance.crypto.toFixed(4)} {balance.symbol}</div>
                </>
              ) : (
                <div className="text-6xl font-bold mb-2 text-red-300">Error</div>
              )}
              
              <Button 
                onClick={() => refetchBalance()}
                className="mt-4 bg-white bg-opacity-20 hover:bg-opacity-30 transition-all duration-200 text-white font-medium"
                size="sm"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh Balance
              </Button>
            </div>
            
            {/* Withdraw Section */}
            <div className="space-y-6">
              <h3 className="text-2xl font-semibold text-neutral-dark text-center">
                How much would you like to withdraw?
              </h3>
              
              {/* Predefined Amount Buttons */}
              <div className="grid grid-cols-2 gap-4">
                {PREDEFINED_AMOUNTS.map((amount) => (
                  <Button
                    key={amount}
                    onClick={() => handleAmountSelect(amount)}
                    variant={selectedAmount === amount ? "default" : "outline"}
                    className={`h-16 text-2xl font-semibold transition-all duration-200 ${
                      selectedAmount === amount 
                        ? 'bg-primary text-white' 
                        : 'bg-neutral border-2 border-gray-300 text-neutral-dark hover:border-primary hover:bg-blue-50'
                    }`}
                  >
                    ${amount}
                  </Button>
                ))}
              </div>
              
              {/* Custom Amount Input */}
              <div className="border-t pt-6">
                <label className="block text-lg font-medium text-neutral-dark mb-3">
                  Or enter custom amount:
                </label>
                <div className="flex space-x-4">
                  <div className="flex-1 relative">
                    <DollarSign className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-500" />
                    <Input
                      type="number"
                      placeholder="0.00"
                      value={customAmount}
                      onChange={(e) => setCustomAmount(e.target.value)}
                      className="pl-12 h-16 text-2xl font-semibold border-2"
                      min="1"
                      max="500"
                      step="0.25"
                    />
                  </div>
                  <Button
                    onClick={handleCustomAmountSelect}
                    className="h-16 px-8 text-xl font-semibold bg-primary hover:bg-primary-dark"
                  >
                    Select
                  </Button>
                </div>
              </div>
            </div>
          </div>
          
          {/* Action Buttons */}
          <div className="flex space-x-6">
            <Button
              onClick={handleStartWithdraw}
              disabled={selectedAmount <= 0 || !isReady}
              className="flex-1 h-16 text-2xl font-bold bg-green-600 hover:bg-green-700 text-white shadow-lg"
            >
              <DollarSign className="w-6 h-6 mr-3" />
              Withdraw Cash
            </Button>
            <Button
              onClick={() => {
                setSelectedAmount(0);
                setCustomAmount("");
                setCurrentActionId("");
              }}
              variant="secondary"
              className="h-16 px-8 text-xl font-bold shadow-lg"
            >
              Cancel
            </Button>
          </div>
        </div>

        {/* Right Panel */}
        <div className="w-1/3 bg-white bg-opacity-10 p-8 flex flex-col">
          {/* Instructions Card */}
          <Card className="flex-1 mb-8">
            <CardContent className="p-8">
              <h3 className="text-2xl font-bold text-neutral-dark mb-6 flex items-center">
                <Info className="text-primary mr-3" />
                How It Works
              </h3>
              
              <div className="space-y-6">
                <div className="flex items-start space-x-4">
                  <div className="w-8 h-8 bg-primary text-white rounded-full flex items-center justify-center font-bold">1</div>
                  <div>
                    <h4 className="font-semibold text-neutral-dark">Select Amount</h4>
                    <p className="text-gray-600">Choose how much cash you want to withdraw</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-4">
                  <div className="w-8 h-8 bg-primary text-white rounded-full flex items-center justify-center font-bold">2</div>
                  <div>
                    <h4 className="font-semibold text-neutral-dark">Verify Identity</h4>
                    <p className="text-gray-600">Scan QR code with your Worldcoin app</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-4">
                  <div className="w-8 h-8 bg-primary text-white rounded-full flex items-center justify-center font-bold">3</div>
                  <div>
                    <h4 className="font-semibold text-neutral-dark">Receive Cash</h4>
                    <p className="text-gray-600">Collect your quarters from the dispenser</p>
                  </div>
                </div>
              </div>
              
              {/* Security Badges */}
              <div className="mt-8 pt-6 border-t border-gray-200">
                <div className="flex items-center justify-center space-x-6">
                  <div className="flex items-center space-x-2">
                    <Shield className="w-4 h-4 text-green-600" />
                    <span className="text-sm font-medium text-gray-700">Secure</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Bolt className="w-4 h-4 text-orange-600" />
                    <span className="text-sm font-medium text-gray-700">Instant</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <UserCheck className="w-4 h-4 text-primary" />
                    <span className="text-sm font-medium text-gray-700">Verified</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          {/* Hardware Status */}
          <Card>
            <CardContent className="p-6">
              <h3 className="text-lg font-bold text-neutral-dark mb-4 flex items-center">
                <Settings className="text-gray-500 mr-2" />
                System Status
              </h3>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-gray-700">Coin Dispenser</span>
                  <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${hardwareStatus ? getStatusDot(hardwareStatus.coinDispenser) : 'bg-gray-500'}`} />
                    <span className={`text-sm font-medium ${hardwareStatus ? getStatusColor(hardwareStatus.coinDispenser) : 'text-gray-500'}`}>
                      {hardwareStatus?.coinDispenser || 'Unknown'}
                    </span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-gray-700">Network</span>
                  <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${hardwareStatus ? getStatusDot(hardwareStatus.network) : 'bg-gray-500'}`} />
                    <span className={`text-sm font-medium ${hardwareStatus ? getStatusColor(hardwareStatus.network) : 'text-gray-500'}`}>
                      {hardwareStatus?.network || 'Unknown'}
                    </span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-gray-700">Security</span>
                  <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${hardwareStatus ? getStatusDot(hardwareStatus.security) : 'bg-gray-500'}`} />
                    <span className={`text-sm font-medium ${hardwareStatus ? getStatusColor(hardwareStatus.security) : 'text-gray-500'}`}>
                      {hardwareStatus?.security || 'Unknown'}
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>

      {/* Footer Bar */}
      <footer className="bg-white bg-opacity-10 px-8 py-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-6">
            <Button className="bg-white bg-opacity-20 hover:bg-opacity-30 text-white font-medium">
              <Headphones className="w-4 h-4 mr-2" />
              Support
            </Button>
            <Button className="bg-red-600 hover:bg-red-700 text-white font-medium">
              <AlertTriangle className="w-4 h-4 mr-2" />
              Emergency Stop
            </Button>
          </div>
          
          <div className="text-white text-sm opacity-75">
            <span>Version 1.0.0 | ID: ATM-001</span>
          </div>
        </div>
      </footer>

      {/* World ID Modal */}
      {showWorldIdModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="max-w-md w-full mx-8">
            <CardContent className="p-12 text-center">
              <div className="mb-6">
                <div className="w-20 h-20 bg-primary rounded-full flex items-center justify-center mx-auto mb-4">
                  <Wifi className="text-white text-2xl" />
                </div>
                <h3 className="text-2xl font-bold text-neutral-dark">Verify with World ID</h3>
                <p className="text-gray-600 mt-2">Scan the QR code with your Worldcoin app</p>
              </div>
              
              <div className="bg-gray-100 rounded-2xl p-8 mb-6">
                <QrCode 
                  value={`worldcoin://verify?action=atm-demo-${Date.now()}&signal=withdraw`}
                  size={192}
                  className="mx-auto"
                />
                <p className="text-sm text-gray-600 mt-4">
                  Withdrawal Amount: <span className="font-bold">${selectedAmount.toFixed(2)}</span>
                </p>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center justify-center space-x-2">
                  <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                  <span className="text-gray-600">Waiting for verification...</span>
                </div>
                
                <div className="flex space-x-4">
                  <Button
                    onClick={handleWorldIdVerify}
                    className="flex-1 bg-primary hover:bg-primary-dark"
                  >
                    Verify Now
                  </Button>
                  <Button
                    onClick={() => setShowWorldIdModal(false)}
                    variant="outline"
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Processing Modal */}
      {showProcessingModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="max-w-md w-full mx-8">
            <CardContent className="p-12 text-center">
              <div className="mb-6">
                <div className="w-20 h-20 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Settings className="text-white text-2xl animate-spin" />
                </div>
                <h3 className="text-2xl font-bold text-neutral-dark">Processing Withdrawal</h3>
                <p className="text-gray-600 mt-2">Please wait while we dispense your cash</p>
              </div>
              
              <div className="space-y-4 mb-6">
                <div className="flex items-center space-x-3">
                  <Check className="w-6 h-6 text-green-600" />
                  <span className="text-gray-700">Identity verified</span>
                </div>
                
                <div className="flex items-center space-x-3">
                  <Check className="w-6 h-6 text-green-600" />
                  <span className="text-gray-700">Funds locked</span>
                </div>
                
                <div className="flex items-center space-x-3">
                  <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                  <span className="text-gray-700">Dispensing coins...</span>
                </div>
              </div>
              
              <div className="bg-blue-50 rounded-xl p-4">
                <p className="text-sm text-primary font-medium">
                  <Info className="w-4 h-4 inline mr-2" />
                  Your cash will be dispensed as quarters (25¢ coins)
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Success Modal */}
      {showSuccessModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="max-w-md w-full mx-8">
            <CardContent className="p-12 text-center">
              <div className="mb-6">
                <div className="w-20 h-20 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Check className="text-white text-3xl" />
                </div>
                <h3 className="text-2xl font-bold text-green-600">Transaction Complete!</h3>
                <p className="text-gray-600 mt-2">Please collect your cash from the dispenser</p>
              </div>
              
              <div className="bg-gray-50 rounded-xl p-6 mb-6">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Amount:</span>
                    <span className="font-semibold">${selectedAmount.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Coins dispensed:</span>
                    <span className="font-semibold">{Math.ceil(selectedAmount / 0.25)} quarters</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Transaction ID:</span>
                    <span className="font-mono text-sm">WC-{new Date().toISOString().slice(0,10).replace(/-/g,'')}-{Math.floor(Math.random() * 9999).toString().padStart(4, '0')}</span>
                  </div>
                </div>
              </div>
              
              <Button
                onClick={handleNewTransaction}
                className="w-full h-12 text-xl font-bold bg-primary hover:bg-primary-dark"
              >
                Start New Transaction
              </Button>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
