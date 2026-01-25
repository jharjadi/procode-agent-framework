"use client";

import React, { useState, useEffect } from "react";
import { Activity, Brain, CheckCircle2, Loader2 } from "lucide-react";

export function AgentStatus() {
  const [status, setStatus] = useState<"idle" | "thinking" | "executing" | "success">("idle");
  const [currentTask, setCurrentTask] = useState("Ready");
  const [intent, setIntent] = useState<string | null>(null);
  const [model, setModel] = useState<"deterministic" | "cached" | "haiku" | "sonnet">("deterministic");

  const statusConfig = {
    idle: {
      icon: CheckCircle2,
      color: "text-green-500",
      bg: "bg-green-500/10",
      border: "border-green-500/20",
      label: "Ready",
    },
    thinking: {
      icon: Brain,
      color: "text-blue-500",
      bg: "bg-blue-500/10",
      border: "border-blue-500/20",
      label: "Analyzing",
    },
    executing: {
      icon: Loader2,
      color: "text-yellow-500",
      bg: "bg-yellow-500/10",
      border: "border-yellow-500/20",
      label: "Executing",
    },
    success: {
      icon: CheckCircle2,
      color: "text-green-500",
      bg: "bg-green-500/10",
      border: "border-green-500/20",
      label: "Complete",
    },
  };

  const modelConfig = {
    deterministic: {
      label: "Deterministic",
      color: "text-green-600",
      bg: "bg-green-500/10",
      cost: "FREE",
    },
    cached: {
      label: "Cached",
      color: "text-blue-600",
      bg: "bg-blue-500/10",
      cost: "FREE",
    },
    haiku: {
      label: "Claude Haiku",
      color: "text-yellow-600",
      bg: "bg-yellow-500/10",
      cost: "$0.0001",
    },
    sonnet: {
      label: "Claude Sonnet",
      color: "text-red-600",
      bg: "bg-red-500/10",
      cost: "$0.001",
    },
  };

  const config = statusConfig[status];
  const Icon = config.icon;
  const modelInfo = modelConfig[model];

  return (
    <div className="lg:col-span-1 bg-card border border-border rounded-lg p-6">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="w-5 h-5 text-primary" />
        <h3 className="font-semibold">Agent Status</h3>
      </div>

      {/* Status Badge */}
      <div className={`flex items-center gap-3 p-4 rounded-lg ${config.bg} border ${config.border} mb-4`}>
        <Icon className={`w-6 h-6 ${config.color} ${status === "executing" ? "animate-spin" : ""}`} />
        <div className="flex-1">
          <p className={`font-medium ${config.color}`}>{config.label}</p>
          <p className="text-sm text-muted-foreground">{currentTask}</p>
        </div>
      </div>

      {/* Intent */}
      {intent && (
        <div className="mb-4">
          <p className="text-xs text-muted-foreground mb-1">Detected Intent</p>
          <div className="px-3 py-2 bg-secondary rounded-md">
            <p className="text-sm font-medium capitalize">{intent}</p>
          </div>
        </div>
      )}

      {/* Model Used */}
      <div>
        <p className="text-xs text-muted-foreground mb-1">Model Used</p>
        <div className={`px-3 py-2 ${modelInfo.bg} rounded-md flex items-center justify-between`}>
          <p className={`text-sm font-medium ${modelInfo.color}`}>{modelInfo.label}</p>
          <p className={`text-xs font-semibold ${modelInfo.color}`}>{modelInfo.cost}</p>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="mt-4 pt-4 border-t border-border">
        <div className="grid grid-cols-2 gap-3 text-center">
          <div>
            <p className="text-2xl font-bold text-foreground">&lt; 200ms</p>
            <p className="text-xs text-muted-foreground">Avg Response</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-green-600">98%</p>
            <p className="text-xs text-muted-foreground">Cost Savings</p>
          </div>
        </div>
      </div>
    </div>
  );
}
