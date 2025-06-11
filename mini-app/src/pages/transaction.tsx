import React, { useState, useEffect } from "react";
import { useRoute } from "wouter";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";
import { useWorldId } from "@/hooks/useWorldId";
import { apiRequest } from "@/lib/queryClient";
import { 
  Coins, 
  Shield, 
  Check,
  X,
  DollarSign,
  AlertTriangle,
  Clock,
  Info,
  Loader2
} from "lucide-react";

interface Transaction {
  id: string;
  amount: number;
  quarters: number;
  total: number;
  status: "pending" | "paid" | "dispensing" | "complete" | "failed" | "expired";
  created_at: string;
  expires_at: string;
}

interface PaymentRequest {
  transaction_id: string;
  proof: string;
  nullifier_hash: string;
  merkle_root: string;
}

export default function TransactionPage() {
  const [match, params] = useRoute("/transaction/:id");
  const [isVerifying, setIsVerifying] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState<"idle" | "processing" | "success" | "error">("idle");
  const { toast } = useToast();
  const worldId = useWorldId();

  // Get transaction ID from URL params or from URL search params for deep links
  const transactionId = params?.id || new URLSearchParams(window.location.search).get('transaction_id');

  // Fetch transaction details
  const { data: transaction, isLoading, error } = useQuery<Transaction>({
    queryKey: ["/api/transaction", transactionId],
    queryFn: async () => {
      if (!transactionId) throw new Error("No transaction ID provided");
      return await apiRequest(`/api/transaction/${transactionId}`);
    },
    enabled: !!transactionId,
    refetchInterval: 2000, // Poll for status updates
  });

  // Payment mutation
  const paymentMutation = useMutation({
    mutationFn: async (data: PaymentRequest) => {
      return await apiRequest("/api/transaction/pay", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      setPaymentStatus("success");
      toast({
        title: "Payment Successful!",
        description: "Your quarters are being dispensed at the kiosk.",
      });
    },
    onError: (error) => {
      setPaymentStatus("error");
      toast({
        title: "Payment Failed",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const handlePayment = async () => {
    if (!transaction || !worldId.isReady) {
      toast({
        title: "Not Ready",
        description: "Please wait for World ID to initialize.",
        variant: "destructive",
      });
      return;
    }

    setIsVerifying(true);
    setPaymentStatus("processing");

    try {
      // Verify World ID
      const proof = await worldId.verify(
        `rolu-atm-${transaction.id}`,
        "payment"
      );

      // Process payment
      await paymentMutation.mutateAsync({
        transaction_id: transaction.id,
        proof: proof.proof,
        nullifier_hash: proof.nullifier_hash,
        merkle_root: proof.merkle_root,
      });

    } catch (error: any) {
      setPaymentStatus("error");
      toast({
        title: "Verification Failed",
        description: error.message || "World ID verification was cancelled or failed",
        variant: "destructive",
      });
    } finally {
      setIsVerifying(false);
    }
  };

  const getTimeRemaining = (expiresAt: string) => {
    const now = new Date();
    const expiry = new Date(expiresAt);
    const diff = expiry.getTime() - now.getTime();
    
    if (diff <= 0) return "Expired";
    
    const minutes = Math.floor(diff / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);
    
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="p-8 text-center">
            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-primary" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Loading Transaction</h2>
            <p className="text-gray-600">Please wait...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Error state
  if (error || !transaction) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-pink-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="p-8 text-center">
            <X className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Transaction Not Found</h2>
            <p className="text-gray-600 mb-4">
              The transaction you're looking for doesn't exist or has expired.
            </p>
            <Button 
              onClick={() => window.close()}
              variant="outline"
              className="w-full"
            >
              Close
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Transaction expired
  if (transaction.status === "expired" || new Date(transaction.expires_at) < new Date()) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 to-yellow-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="p-8 text-center">
            <Clock className="w-12 h-12 text-orange-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Transaction Expired</h2>
            <p className="text-gray-600 mb-4">
              This transaction has expired. Please start a new transaction at the kiosk.
            </p>
            <Button 
              onClick={() => window.close()}
              variant="outline"
              className="w-full"
            >
              Close
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Transaction already completed
  if (transaction.status === "complete") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="p-8 text-center">
            <Check className="w-12 h-12 text-green-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Transaction Complete</h2>
            <p className="text-gray-600 mb-6">
              Your quarters have been dispensed at the kiosk.
            </p>
            
            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Amount:</span>
                  <span className="font-semibold">${transaction.amount.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Quarters:</span>
                  <span className="font-semibold">{transaction.quarters}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Transaction ID:</span>
                  <span className="font-mono text-xs">{transaction.id}</span>
                </div>
              </div>
            </div>
            
            <Button 
              onClick={() => window.close()}
              className="w-full bg-green-600 hover:bg-green-700"
            >
              Close
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Payment success - waiting for dispensing
  if (paymentStatus === "success" || transaction.status === "paid" || transaction.status === "dispensing") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="p-8 text-center">
            <div className="w-16 h-16 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <Check className="w-8 h-8 text-white" />
            </div>
            
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Payment Successful!</h2>
            <p className="text-gray-600 mb-6">
              {transaction.status === "dispensing" 
                ? "Your quarters are being dispensed..."
                : "Processing your transaction..."}
            </p>
            
            {transaction.status === "dispensing" && (
              <div className="mb-6">
                <Progress value={75} className="h-2 mb-2" />
                <p className="text-sm text-gray-600">Dispensing in progress...</p>
              </div>
            )}
            
            <div className="bg-white rounded-lg p-4 mb-6 border">
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Amount:</span>
                  <span className="font-semibold">${transaction.amount.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Quarters:</span>
                  <span className="font-semibold">{transaction.quarters}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Paid:</span>
                  <span className="font-semibold text-green-600">${transaction.total.toFixed(2)}</span>
                </div>
              </div>
            </div>
            
            <div className="bg-blue-50 rounded-lg p-4 mb-6">
              <Info className="w-5 h-5 text-blue-600 mx-auto mb-2" />
              <p className="text-sm text-blue-800">
                Please collect your quarters from the kiosk dispenser.
              </p>
            </div>
            
            <Button 
              onClick={() => window.close()}
              variant="outline"
              className="w-full"
            >
              Close
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Main payment screen
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardContent className="p-8">
          {/* Header */}
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-primary rounded-full flex items-center justify-center mx-auto mb-4">
              <Coins className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">RoluATM</h1>
            <p className="text-gray-600">Complete your transaction</p>
          </div>

          {/* Transaction Details */}
          <div className="bg-white rounded-lg p-4 mb-6 border">
            <h3 className="font-semibold text-gray-900 mb-3">Transaction Summary</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Amount:</span>
                <span className="font-semibold">${transaction.amount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Fee:</span>
                <span className="font-semibold">$0.50</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Quarters:</span>
                <span className="font-semibold">{transaction.quarters}</span>
              </div>
              <div className="flex justify-between border-t pt-2">
                <span className="font-semibold text-gray-900">Total:</span>
                <span className="font-bold text-primary">${transaction.total.toFixed(2)}</span>
              </div>
            </div>
          </div>

          {/* Time Remaining */}
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 mb-6">
            <div className="flex items-center space-x-2">
              <Clock className="w-4 h-4 text-orange-600" />
              <span className="text-sm font-medium text-orange-800">
                Time remaining: {getTimeRemaining(transaction.expires_at)}
              </span>
            </div>
          </div>

          {/* World ID Section */}
          <div className="mb-6">
            <div className="flex items-center space-x-3 mb-4">
              <Shield className="w-5 h-5 text-green-600" />
              <span className="font-semibold text-gray-900">Secure with World ID</span>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Verify your identity and complete payment with your World ID.
            </p>
            
            {!worldId.isReady && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
                <div className="flex items-center space-x-2">
                  <Loader2 className="w-4 h-4 text-yellow-600 animate-spin" />
                  <span className="text-sm text-yellow-800">Initializing World ID...</span>
                </div>
              </div>
            )}
          </div>

          {/* Payment Button */}
          <Button
            onClick={handlePayment}
            disabled={!worldId.isReady || isVerifying || paymentStatus === "processing"}
            className="w-full h-12 text-lg font-semibold bg-green-600 hover:bg-green-700 mb-4"
          >
            {isVerifying || paymentStatus === "processing" ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                {isVerifying ? "Verifying..." : "Processing..."}
              </>
            ) : (
              <>
                <DollarSign className="w-5 h-5 mr-2" />
                Pay ${transaction.total.toFixed(2)}
              </>
            )}
          </Button>

          {/* Error State */}
          {paymentStatus === "error" && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-red-600" />
                <span className="text-sm text-red-800">Payment failed. Please try again.</span>
              </div>
            </div>
          )}

          {/* Cancel Button */}
          <Button
            onClick={() => window.close()}
            variant="outline"
            className="w-full"
            disabled={isVerifying || paymentStatus === "processing"}
          >
            Cancel
          </Button>
        </CardContent>
      </Card>
    </div>
  );
} 