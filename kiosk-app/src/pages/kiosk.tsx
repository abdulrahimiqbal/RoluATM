import React, { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";
import { QrCode } from "@/components/Qr";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { 
  Coins, 
  Settings, 
  DollarSign,
  Check,
  Clock,
  Info,
  Wifi,
  AlertTriangle,
  Headphones,
  RefreshCw,
  X,
  Database,
  Server,
  Shield,
  WifiOff,
  AlertCircle,
  CheckCircle
} from "lucide-react";

interface HardwareStatus {
  coinDispenser: "ready" | "low" | "fault";
  network: "connected" | "disconnected";
  security: "active" | "inactive";
}

interface SystemHealth {
  status: "healthy" | "degraded" | "unhealthy";
  backend: "online" | "offline";
  database: "connected" | "disconnected" | "error";
  hardware: {
    tflex: "hardware" | "mock" | "error";
  };
  network: "connected" | "disconnected";
  timestamp: string;
}

interface Transaction {
  id: string;
  amount: number;
  quarters: number;
  total: number;
  mini_app_url: string;
  status: "pending" | "paid" | "dispensing" | "completed" | "failed";
  created_at: string;
}

interface CreateTransactionRequest {
  amount: number;
  quarters: number;
  total: number;
}

const PREDEFINED_AMOUNTS = [5, 10, 20, 50];
const COIN_VALUE = 0.25;
const TRANSACTION_FEE = 0.50;

export default function KioskPage() {
  const [selectedAmount, setSelectedAmount] = useState<number>(0);
  const [customAmount, setCustomAmount] = useState<string>("");
  const [currentTransaction, setCurrentTransaction] = useState<Transaction | null>(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [dispensingProgress, setDispensingProgress] = useState(0);
  const { toast } = useToast();

  // Update time every second
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Fetch system health
  const { data: systemHealth, isError: healthError } = useQuery<SystemHealth>({
    queryKey: ["/health"],
    refetchInterval: 3000, // Check every 3 seconds
    retry: 3,
    retryDelay: 1000,
  });

  // Fetch hardware status
  const { data: hardwareStatus } = useQuery<HardwareStatus>({
    queryKey: ["/api/status"],
    refetchInterval: 5000,
  });

  // Poll for transaction status when we have a current transaction
  const { data: transactionStatus } = useQuery({
    queryKey: ["/api/transaction", currentTransaction?.id],
    queryFn: async () => {
      if (!currentTransaction) return null;
      const response = await apiRequest("GET", `/api/transaction/${currentTransaction.id}`);
      return response.json();
    },
    enabled: !!currentTransaction,
    refetchInterval: 2000, // Poll every 2 seconds
  });

  // Update local transaction state when backend status changes
  useEffect(() => {
    if (transactionStatus && currentTransaction && transactionStatus.id === currentTransaction.id) {
      // Only update if the status actually changed
      if (transactionStatus.status !== currentTransaction.status) {
        setCurrentTransaction(prev => prev ? { ...prev, ...transactionStatus } : null);
        
        // Handle dispensing progress
        if (transactionStatus.status === "dispensing" && transactionStatus.progress) {
          setDispensingProgress(transactionStatus.progress);
        }
        
        // Handle completion
        if (transactionStatus.status === "completed") {
          setDispensingProgress(100);
          toast({
            title: "Transaction Complete!",
            description: `${transactionStatus.quarters} quarters have been dispensed.`,
          });
        }
        
        // Handle failures
        if (transactionStatus.status === "failed") {
          toast({
            title: "Transaction Failed",
            description: transactionStatus.error || "Something went wrong.",
            variant: "destructive",
          });
        }
      }
    }
  }, [transactionStatus, toast]); // Removed currentTransaction from dependencies

  // Create transaction mutation
  const createTransactionMutation = useMutation({
    mutationFn: async (data: CreateTransactionRequest) => {
      const response = await apiRequest("POST", "/api/transaction/create", data);
      return response.json();
    },
    onSuccess: (data) => {
      setCurrentTransaction(data);
      toast({
        title: "QR Code Generated",
        description: "Scan with your World App to complete payment",
      });
    },
    onError: (error) => {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  // Check if system is ready for transactions
  const isSystemReady = () => {
    if (healthError || !systemHealth) return false;
    
    return (
      systemHealth.status === "healthy" &&
      systemHealth.backend === "online" &&
      systemHealth.database === "connected" &&
      (systemHealth.hardware.tflex === "hardware" || systemHealth.hardware.tflex === "mock")
    );
  };

  // Get system status indicator
  const getSystemStatusIndicator = () => {
    if (healthError || !systemHealth) {
      return {
        color: "bg-red-500",
        text: "System Offline",
        icon: AlertCircle,
        textColor: "text-red-600"
      };
    }

    if (systemHealth.status === "healthy" && isSystemReady()) {
      return {
        color: "bg-green-500",
        text: "All Systems Ready",
        icon: CheckCircle,
        textColor: "text-green-600"
      };
    }

    if (systemHealth.status === "degraded") {
      return {
        color: "bg-yellow-500",
        text: "System Degraded",
        icon: AlertTriangle,
        textColor: "text-yellow-600"
      };
    }

    return {
      color: "bg-red-500",
      text: "System Error",
      icon: AlertCircle,
      textColor: "text-red-600"
    };
  };

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

  const handleCreateTransaction = () => {
    if (!isSystemReady()) {
      toast({
        title: "System Not Ready",
        description: "Please wait for all systems to come online before creating a transaction",
        variant: "destructive",
      });
      return;
    }

    if (selectedAmount <= 0) {
      toast({
        title: "Select Amount",
        description: "Please select an amount to withdraw",
        variant: "destructive",
      });
      return;
    }

    const quarters = Math.ceil(selectedAmount / COIN_VALUE);
    const total = selectedAmount + TRANSACTION_FEE;

    createTransactionMutation.mutate({
      amount: selectedAmount,
      quarters,
      total,
    });
  };

  const handleNewTransaction = () => {
    setCurrentTransaction(null);
    setSelectedAmount(0);
    setCustomAmount("");
    setDispensingProgress(0);
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

  // Handle exit/close browser
  const handleExit = () => {
    // Try multiple methods to close the browser/app
    if (window.confirm("Are you sure you want to exit the kiosk?")) {
      // For kiosk mode browsers
      if (window.close) {
        window.close();
      }
      // For Electron apps
      if (window.electronAPI?.closeApp) {
        window.electronAPI.closeApp();
      }
      // For PWA/fullscreen mode
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
      // Fallback - navigate to a blank page
      window.location.href = "about:blank";
    }
  };

  const systemStatusIndicator = getSystemStatusIndicator();

  // Show QR code screen when transaction is created
  if (currentTransaction && currentTransaction.status === "pending") {
    return (
      <div className="h-screen flex flex-col gradient-primary">
        <header className="bg-white shadow-lg px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center">
              <Coins className="text-white text-xl" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-neutral-dark">RoluATM</h1>
              <p className="text-sm text-gray-600">Scan to Complete Payment</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <div className="text-lg font-semibold text-neutral-dark">
                {currentTime.toLocaleTimeString('en-US', { 
                  hour: 'numeric', 
                  minute: '2-digit', 
                  hour12: true 
                })}
              </div>
            </div>
            <Button
              onClick={handleExit}
              variant="ghost"
              size="sm"
              className="w-10 h-10 p-0 text-gray-500 hover:text-red-500 hover:bg-red-50"
            >
              <X className="w-6 h-6" />
            </Button>
          </div>
        </header>

        <main className="flex-1 flex items-center justify-center p-8">
          <Card className="max-w-2xl w-full">
            <CardContent className="p-12 text-center">
              <div className="mb-8">
                <h2 className="text-3xl font-bold text-neutral-dark mb-4">
                  Scan QR Code with World App
                </h2>
                <p className="text-xl text-gray-600">
                  Complete your payment to receive {currentTransaction.quarters} quarters
                </p>
              </div>

              <div className="bg-white rounded-3xl p-8 mb-8 shadow-inner">
                <QrCode 
                  value={currentTransaction.mini_app_url}
                  size={300}
                  className="mx-auto"
                />
              </div>

              <div className="bg-gray-50 rounded-xl p-6 mb-8">
                <div className="grid grid-cols-2 gap-4 text-lg">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Amount:</span>
                    <span className="font-semibold">${currentTransaction.amount.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Fee:</span>
                    <span className="font-semibold">$0.50</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Quarters:</span>
                    <span className="font-semibold">{currentTransaction.quarters}</span>
                  </div>
                  <div className="flex justify-between border-t pt-2">
                    <span className="text-gray-800 font-semibold">Total:</span>
                    <span className="font-bold text-primary">${currentTransaction.total.toFixed(2)}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-center space-x-2 mb-6">
                <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                <span className="text-gray-600">Waiting for payment...</span>
              </div>

              <Button
                onClick={handleNewTransaction}
                variant="outline"
                className="w-full"
              >
                Cancel Transaction
              </Button>
            </CardContent>
          </Card>
        </main>
      </div>
    );
  }

  // Show dispensing screen
  if (currentTransaction && (currentTransaction.status === "paid" || currentTransaction.status === "dispensing")) {
    return (
      <div className="h-screen flex flex-col gradient-primary">
        <header className="bg-white shadow-lg px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center">
              <Coins className="text-white text-xl" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-neutral-dark">RoluATM</h1>
              <p className="text-sm text-gray-600">Dispensing Quarters</p>
            </div>
          </div>
          <Button
            onClick={handleExit}
            variant="ghost"
            size="sm"
            className="w-10 h-10 p-0 text-gray-500 hover:text-red-500 hover:bg-red-50"
          >
            <X className="w-6 h-6" />
          </Button>
        </header>

        <main className="flex-1 flex items-center justify-center p-8">
          <Card className="max-w-2xl w-full">
            <CardContent className="p-12 text-center">
              <div className="mb-8">
                <div className="w-20 h-20 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Settings className="text-white text-3xl animate-spin" />
                </div>
                <h2 className="text-3xl font-bold text-green-600 mb-4">
                  Payment Received!
                </h2>
                <p className="text-xl text-gray-600">
                  Dispensing your quarters...
                </p>
              </div>

              <div className="mb-8">
                <Progress value={dispensingProgress} className="h-4 mb-4" />
                <p className="text-lg font-semibold">
                  {Math.floor((dispensingProgress / 100) * currentTransaction.quarters)} / {currentTransaction.quarters} quarters dispensed
                </p>
              </div>

              <div className="bg-blue-50 rounded-xl p-4">
                <p className="text-sm text-primary font-medium">
                  <Info className="w-4 h-4 inline mr-2" />
                  Please collect your quarters from the tray below
                </p>
              </div>
            </CardContent>
          </Card>
        </main>
      </div>
    );
  }

  // Show success screen
  if (currentTransaction && currentTransaction.status === "completed") {
    return (
      <div className="h-screen flex flex-col gradient-primary">
        <header className="bg-white shadow-lg px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center">
              <Check className="text-white text-xl" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-neutral-dark">RoluATM</h1>
              <p className="text-sm text-gray-600">Transaction Complete</p>
            </div>
          </div>
          <Button
            onClick={handleExit}
            variant="ghost"
            size="sm"
            className="w-10 h-10 p-0 text-gray-500 hover:text-red-500 hover:bg-red-50"
          >
            <X className="w-6 h-6" />
          </Button>
        </header>

        <main className="flex-1 flex items-center justify-center p-8">
          <Card className="max-w-2xl w-full">
            <CardContent className="p-12 text-center">
              <div className="mb-8">
                <div className="w-20 h-20 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Check className="text-white text-3xl" />
                </div>
                <h2 className="text-3xl font-bold text-green-600 mb-4">
                  Transaction Complete!
                </h2>
                <p className="text-xl text-gray-600">
                  Your {currentTransaction.quarters} quarters have been dispensed
                </p>
              </div>

              <div className="bg-green-50 rounded-xl p-6 mb-8">
                <div className="text-lg">
                  <div className="flex justify-between mb-2">
                    <span className="text-gray-600">Amount Withdrawn:</span>
                    <span className="font-semibold">${currentTransaction.amount.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between mb-2">
                    <span className="text-gray-600">Quarters Dispensed:</span>
                    <span className="font-semibold">{currentTransaction.quarters}</span>
                  </div>
                  <div className="flex justify-between border-t pt-2">
                    <span className="text-gray-800 font-semibold">Total Paid:</span>
                    <span className="font-bold text-green-600">${currentTransaction.total.toFixed(2)}</span>
                  </div>
                </div>
              </div>

              <div className="bg-blue-50 rounded-xl p-4 mb-8">
                <p className="text-sm text-primary font-medium">
                  <Info className="w-4 h-4 inline mr-2" />
                  Thank you for using RoluATM! Please collect all your quarters.
                </p>
              </div>

              <Button
                onClick={handleNewTransaction}
                className="w-full h-16 text-xl font-bold bg-primary hover:bg-primary-dark"
              >
                Start New Transaction
              </Button>
            </CardContent>
          </Card>
        </main>
      </div>
    );
  }

  // Main interface
  return (
    <div className="h-screen flex flex-col gradient-primary">
      {/* Header */}
      <header className="bg-white shadow-lg px-8 py-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center">
              <Coins className="text-white text-xl" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-neutral-dark">RoluATM</h1>
              <p className="text-sm text-gray-600">Crypto to Cash Kiosk</p>
            </div>
          </div>

          {/* System Status Indicator */}
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-3 bg-gray-50 rounded-lg px-4 py-2">
              <div className={`w-3 h-3 rounded-full ${systemStatusIndicator.color} animate-pulse`} />
              <div className="flex items-center space-x-2">
                <systemStatusIndicator.icon className={`w-4 h-4 ${systemStatusIndicator.textColor}`} />
                <span className={`text-sm font-medium ${systemStatusIndicator.textColor}`}>
                  {systemStatusIndicator.text}
                </span>
              </div>
            </div>

            {/* Detailed System Status */}
            {systemHealth && (
              <div className="flex items-center space-x-4 text-xs">
                <div className="flex items-center space-x-1">
                  <Server className={`w-3 h-3 ${systemHealth.backend === 'online' ? 'text-green-500' : 'text-red-500'}`} />
                  <span className={systemHealth.backend === 'online' ? 'text-green-600' : 'text-red-600'}>
                    Backend
                  </span>
                </div>
                <div className="flex items-center space-x-1">
                  <Database className={`w-3 h-3 ${systemHealth.database === 'connected' ? 'text-green-500' : 'text-red-500'}`} />
                  <span className={systemHealth.database === 'connected' ? 'text-green-600' : 'text-red-600'}>
                    Database
                  </span>
                </div>
                <div className="flex items-center space-x-1">
                  <Coins className={`w-3 h-3 ${systemHealth.hardware.tflex !== 'error' ? 'text-green-500' : 'text-red-500'}`} />
                  <span className={systemHealth.hardware.tflex !== 'error' ? 'text-green-600' : 'text-red-600'}>
                    Hardware
                  </span>
                </div>
                <div className="flex items-center space-x-1">
                  {hardwareStatus?.network === 'connected' ? (
                    <Wifi className="w-3 h-3 text-green-500" />
                  ) : (
                    <WifiOff className="w-3 h-3 text-red-500" />
                  )}
                  <span className={hardwareStatus?.network === 'connected' ? 'text-green-600' : 'text-red-600'}>
                    Network
                  </span>
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center space-x-4">
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

            {/* Exit Button */}
            <Button
              onClick={handleExit}
              variant="ghost"
              size="sm"
              className="w-10 h-10 p-0 text-gray-500 hover:text-red-500 hover:bg-red-50"
            >
              <X className="w-6 h-6" />
            </Button>
          </div>
        </div>

        {/* System Status Warning Banner */}
        {!isSystemReady() && (
          <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-yellow-600" />
              <span className="text-yellow-800 font-medium">
                System not ready for transactions. Please wait for all components to come online.
              </span>
            </div>
          </div>
        )}
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
                    disabled={!isSystemReady()}
                    className={`h-16 text-2xl font-semibold transition-all duration-200 ${
                      selectedAmount === amount 
                        ? 'bg-primary text-white' 
                        : 'bg-neutral border-2 border-gray-300 text-neutral-dark hover:border-primary hover:bg-blue-50'
                    } ${!isSystemReady() ? 'opacity-50 cursor-not-allowed' : ''}`}
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
                      disabled={!isSystemReady()}
                      className="pl-12 h-16 text-2xl font-semibold border-2"
                      min="1"
                      max="500"
                      step="0.25"
                    />
                  </div>
                  <Button
                    onClick={handleCustomAmountSelect}
                    disabled={!isSystemReady()}
                    className="h-16 px-8 text-xl font-semibold bg-primary hover:bg-primary-dark"
                  >
                    Select
                  </Button>
                </div>
              </div>

              {/* Show calculation */}
              {selectedAmount > 0 && (
                <div className="bg-blue-50 rounded-xl p-4">
                  <div className="text-center">
                    <p className="text-sm text-gray-600 mb-2">Transaction Summary:</p>
                    <div className="space-y-1">
                      <div className="flex justify-between">
                        <span>Amount:</span>
                        <span className="font-semibold">${selectedAmount.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Quarters:</span>
                        <span className="font-semibold">{Math.ceil(selectedAmount / COIN_VALUE)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Fee:</span>
                        <span className="font-semibold">$0.50</span>
                      </div>
                      <div className="flex justify-between border-t pt-1">
                        <span className="font-bold">Total:</span>
                        <span className="font-bold text-primary">${(selectedAmount + TRANSACTION_FEE).toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
          
          {/* Action Buttons */}
          <div className="flex space-x-6">
            <Button
              onClick={handleCreateTransaction}
              disabled={selectedAmount <= 0 || createTransactionMutation.isPending || !isSystemReady()}
              className="flex-1 h-16 text-2xl font-bold bg-green-600 hover:bg-green-700 text-white shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {createTransactionMutation.isPending ? (
                <>
                  <RefreshCw className="w-6 h-6 mr-3 animate-spin" />
                  Creating...
                </>
              ) : !isSystemReady() ? (
                <>
                  <AlertTriangle className="w-6 h-6 mr-3" />
                  System Not Ready
                </>
              ) : (
                <>
                  <DollarSign className="w-6 h-6 mr-3" />
                  Generate QR Code
                </>
              )}
            </Button>
            <Button
              onClick={() => {
                setSelectedAmount(0);
                setCustomAmount("");
              }}
              variant="secondary"
              className="h-16 px-8 text-xl font-bold shadow-lg"
            >
              Clear
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
                    <h4 className="font-semibold text-neutral-dark">Scan QR Code</h4>
                    <p className="text-gray-600">Use your World App to scan the generated QR code</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-4">
                  <div className="w-8 h-8 bg-primary text-white rounded-full flex items-center justify-center font-bold">3</div>
                  <div>
                    <h4 className="font-semibold text-neutral-dark">Complete Payment</h4>
                    <p className="text-gray-600">Verify with World ID and pay with your wallet</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-4">
                  <div className="w-8 h-8 bg-primary text-white rounded-full flex items-center justify-center font-bold">4</div>
                  <div>
                    <h4 className="font-semibold text-neutral-dark">Collect Cash</h4>
                    <p className="text-gray-600">Quarters will be dispensed automatically</p>
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

                {/* Additional system info */}
                {systemHealth && (
                  <>
                    <div className="border-t pt-3 mt-3">
                      <div className="flex items-center justify-between">
                        <span className="text-gray-700">Backend</span>
                        <div className="flex items-center space-x-2">
                          <div className={`w-2 h-2 rounded-full ${systemHealth.backend === 'online' ? 'bg-green-500' : 'bg-red-500'}`} />
                          <span className={`text-sm font-medium ${systemHealth.backend === 'online' ? 'text-green-500' : 'text-red-500'}`}>
                            {systemHealth.backend}
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <span className="text-gray-700">Database</span>
                        <div className="flex items-center space-x-2">
                          <div className={`w-2 h-2 rounded-full ${systemHealth.database === 'connected' ? 'bg-green-500' : 'bg-red-500'}`} />
                          <span className={`text-sm font-medium ${systemHealth.database === 'connected' ? 'text-green-500' : 'text-red-500'}`}>
                            {systemHealth.database}
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <span className="text-gray-700">Hardware Mode</span>
                        <div className="flex items-center space-x-2">
                          <div className={`w-2 h-2 rounded-full ${systemHealth.hardware.tflex !== 'error' ? 'bg-green-500' : 'bg-red-500'}`} />
                          <span className={`text-sm font-medium ${systemHealth.hardware.tflex !== 'error' ? 'text-green-500' : 'text-red-500'}`}>
                            {systemHealth.hardware.tflex}
                          </span>
                        </div>
                      </div>
                    </div>
                  </>
                )}
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
            RoluATM v2.0 • Powered by World ID
          </div>
        </div>
      </footer>
    </div>
  );
}
