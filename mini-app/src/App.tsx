import React from "react";
import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { MiniKitProvider } from "@worldcoin/minikit-js/minikit-provider";
import TransactionPage from "@/pages/transaction";
import NotFound from "@/pages/not-found";

function Router() {
  return (
    <Switch>
      <Route path="/" component={TransactionPage} />
      <Route path="/transaction/:id" component={TransactionPage} />
      <Route component={NotFound} />
    </Switch>
  );
}

// Development mode detection
const isDevelopmentMode = () => {
  return window.location.hostname === 'localhost' || 
         window.location.hostname === '127.0.0.1' ||
         window.location.hostname.includes('vercel.app');
};

// Development banner component
function DevelopmentBanner() {
  if (!isDevelopmentMode()) return null;
  
  return (
    <div className="bg-yellow-100 border-b border-yellow-200 px-4 py-2 text-center">
      <p className="text-sm text-yellow-800">
        🔧 <strong>Development Mode:</strong> Running outside World App with mock functionality
      </p>
    </div>
  );
}

function App() {
  const appId = import.meta.env.VITE_WORLD_APP_ID as string;
  
  if (!appId && !isDevelopmentMode()) {
    console.warn("VITE_WORLD_APP_ID not configured. World ID features will not work.");
  }

  return (
    <MiniKitProvider>
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <DevelopmentBanner />
        <Toaster />
        <Router />
      </TooltipProvider>
    </QueryClientProvider>
    </MiniKitProvider>
  );
}

export default App;
