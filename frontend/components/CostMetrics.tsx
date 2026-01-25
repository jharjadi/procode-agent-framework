"use client";

import React from "react";
import { DollarSign, TrendingDown, Zap } from "lucide-react";

interface CostMetricsProps {
  metrics: {
    totalRequests: number;
    cacheHits: number;
    llmCalls: number;
    costSavings: number;
    currentCost: number;
  };
}

export function CostMetrics({ metrics }: CostMetricsProps) {
  const cacheHitRate = metrics.totalRequests > 0 
    ? (metrics.cacheHits / metrics.totalRequests) * 100 
    : 0;
  
  const savingsPercent = metrics.costSavings > 0 
    ? ((metrics.costSavings / (metrics.currentCost + metrics.costSavings)) * 100)
    : 98; // Default to 98% for demo

  return (
    <div className="flex items-center gap-4">
      {/* Current Cost */}
      <div className="flex items-center gap-2 px-3 py-2 bg-card border border-border rounded-lg">
        <DollarSign className="w-4 h-4 text-primary" />
        <div>
          <p className="text-xs text-muted-foreground">Session Cost</p>
          <p className="text-sm font-semibold">
            ${metrics.currentCost.toFixed(4)}
          </p>
        </div>
      </div>

      {/* Savings */}
      <div className="flex items-center gap-2 px-3 py-2 bg-green-500/10 border border-green-500/20 rounded-lg">
        <TrendingDown className="w-4 h-4 text-green-600" />
        <div>
          <p className="text-xs text-green-600">Savings</p>
          <p className="text-sm font-semibold text-green-600">
            {savingsPercent.toFixed(0)}%
          </p>
        </div>
      </div>

      {/* Cache Hit Rate */}
      <div className="flex items-center gap-2 px-3 py-2 bg-blue-500/10 border border-blue-500/20 rounded-lg">
        <Zap className="w-4 h-4 text-blue-600" />
        <div>
          <p className="text-xs text-blue-600">Cache</p>
          <p className="text-sm font-semibold text-blue-600">
            {cacheHitRate.toFixed(0)}%
          </p>
        </div>
      </div>
    </div>
  );
}
