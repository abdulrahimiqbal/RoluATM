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

function App() {
  const appId = import.meta.env.VITE_WORLD_APP_ID as string;
  
  if (!appId) {
    console.warn("VITE_WORLD_APP_ID not configured. World ID features will not work.");
  }

  return (
    <MiniKitProvider>
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <Toaster />
          <Router />
        </TooltipProvider>
      </QueryClientProvider>
    </MiniKitProvider>
  );
}

export default App;
