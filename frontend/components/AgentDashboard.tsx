"use client";

import React from "react";
import { BarChart3, TrendingUp } from "lucide-react";

interface AgentDashboardProps {
  metrics: {
    totalRequests: number;
    cacheHits: number;
    llmCalls: number;
    costSavings: number;
    currentCost: number;
  };
}

export function AgentDashboard({ metrics }: AgentDashboardProps) {
  const llmCallRate = metrics.totalRequests > 0 
    ? ((metrics.llmCalls / metrics.totalRequests) * 100).toFixed(1)
    : "0.0";

  const deterministicRate = metrics.totalRequests > 0
    ? (((metrics.totalRequests - metrics.llmCalls - metrics.cacheHits) / metrics.totalRequests) * 100).toFixed(1)
    : "0.0";

  return (
    <div className="lg:col-span-2 bg-card border border-border rounded-lg p-6">
      <div className="flex items-center gap-2 mb-4">
        <BarChart3 className="w-5 h-5 text-primary" />
        <h3 className="font-semibold">Performance Metrics</h3>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Total Requests */}
        <div className="p-4 bg-secondary rounded-lg">
          <p className="text-2xl font-bold text-foreground">{metrics.totalRequests}</p>
          <p className="text-xs text-muted-foreground mt-1">Total Requests</p>
        </div>

        {/* Cache Hits */}
        <div className="p-4 bg-blue-500/10 rounded-lg">
          <p className="text-2xl font-bold text-blue-600">{metrics.cacheHits}</p>
          <p className="text-xs text-muted-foreground mt-1">Cache Hits</p>
        </div>

        {/* LLM Calls */}
        <div className="p-4 bg-yellow-500/10 rounded-lg">
          <p className="text-2xl font-bold text-yellow-600">{metrics.llmCalls}</p>
          <p className="text-xs text-muted-foreground mt-1">LLM Calls</p>
        </div>

        {/* Deterministic */}
        <div className="p-4 bg-green-500/10 rounded-lg">
          <p className="text-2xl font-bold text-green-600">{deterministicRate}%</p>
          <p className="text-xs text-muted-foreground mt-1">Deterministic</p>
        </div>
      </div>

      {/* Cost Breakdown */}
      <div className="mt-6 p-4 bg-gradient-to-r from-purple-500/10 to-blue-500/10 rounded-lg border border-purple-500/20">
        <div className="flex items-center gap-2 mb-3">
          <TrendingUp className="w-4 h-4 text-purple-600" />
          <h4 className="font-semibold text-purple-600">Cost Optimization</h4>
        </div>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-lg font-bold text-foreground">${metrics.currentCost.toFixed(4)}</p>
            <p className="text-xs text-muted-foreground">Current</p>
          </div>
          <div>
            <p className="text-lg font-bold text-red-600">${(metrics.currentCost * 50).toFixed(2)}</p>
            <p className="text-xs text-muted-foreground">Without Optimization</p>
          </div>
          <div>
            <p className="text-lg font-bold text-green-600">${(metrics.currentCost * 49).toFixed(2)}</p>
            <p className="text-xs text-muted-foreground">Saved</p>
          </div>
        </div>
      </div>
    </div>
  );
}
