"use client";

import React, { useState } from "react";
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import { AgentDashboard } from "@/components/AgentDashboard";
import { CostMetrics } from "@/components/CostMetrics";
import { AgentStatus } from "@/components/AgentStatus";

export default function Home() {
  const [metrics, setMetrics] = useState({
    totalRequests: 0,
    cacheHits: 0,
    llmCalls: 0,
    costSavings: 0,
    currentCost: 0,
  });

  return (
    <CopilotKit runtimeUrl="/api/copilot">
      <div className="flex h-screen bg-background">
        {/* Main Content Area */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <header className="border-b border-border bg-card">
            <div className="container mx-auto px-6 py-4">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-2xl font-bold text-foreground">
                    Procode Agent
                  </h1>
                  <p className="text-sm text-muted-foreground">
                    AI Assistant with 98% Cost Savings
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <CostMetrics metrics={metrics} />
                </div>
              </div>
            </div>
          </header>

          {/* Dashboard */}
          <main className="flex-1 overflow-auto">
            <div className="container mx-auto px-6 py-6">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                <AgentStatus />
                <AgentDashboard metrics={metrics} />
              </div>

              {/* Welcome Message */}
              <div className="bg-card border border-border rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-4">
                  Welcome to Procode Agent! 👋
                </h2>
                <p className="text-muted-foreground mb-4">
                  I'm your AI assistant powered by a cost-optimized multi-LLM
                  strategy. I can help you with:
                </p>
                <ul className="space-y-2 text-muted-foreground">
                  <li className="flex items-center gap-2">
                    <span className="text-green-500">✓</span>
                    <span>
                      <strong>Support Tickets</strong> - Create and manage
                      support tickets
                    </span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-green-500">✓</span>
                    <span>
                      <strong>Account Management</strong> - View and update
                      account information
                    </span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-green-500">✓</span>
                    <span>
                      <strong>General Questions</strong> - Answer questions and
                      provide assistance
                    </span>
                  </li>
                </ul>
                <div className="mt-6 p-4 bg-primary/10 border border-primary/20 rounded-lg">
                  <p className="text-sm font-medium text-primary">
                    💰 Cost Optimization Active
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Using intelligent caching and confidence-based routing to
                    reduce costs by up to 98%
                  </p>
                </div>
              </div>
            </div>
          </main>
        </div>

        {/* CopilotKit Sidebar */}
        <CopilotSidebar
          labels={{
            title: "Chat with Agent",
            initial: "How can I help you today?",
          }}
          defaultOpen={true}
          clickOutsideToClose={false}
        />
      </div>
    </CopilotKit>
  );
}
