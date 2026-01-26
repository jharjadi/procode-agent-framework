"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Loader2 } from "lucide-react";
import { AgentDashboard } from "@/components/AgentDashboard";
import { CostMetrics } from "@/components/CostMetrics";
import { AgentStatus } from "@/components/AgentStatus";

interface Message {
  role: "user" | "assistant";
  content: string;
  metadata?: {
    intent?: string;
    model?: string;
    cost?: number;
  };
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [metrics, setMetrics] = useState({
    totalRequests: 0,
    cacheHits: 0,
    llmCalls: 0,
    costSavings: 0,
    currentCost: 0,
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      // Use environment variable for backend URL, fallback to localhost for development
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:9998/";
      const apiKey = process.env.NEXT_PUBLIC_API_KEY || "";
      
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      
      // Add API key if configured
      if (apiKey) {
        headers["X-API-Key"] = apiKey;
      }
      
      const response = await fetch(backendUrl, {
        method: "POST",
        headers,
        body: JSON.stringify({
          jsonrpc: "2.0",
          method: "message/send",
          params: {
            message: {
              role: "user",
              parts: [
                {
                  kind: "text",
                  text: input,
                },
              ],
              messageId: `msg-${Date.now()}`,
            },
          },
          id: Date.now(),
        }),
      });

      if (!response.ok) {
        throw new Error(`Backend responded with ${response.status}`);
      }

      const data = await response.json();

      const agentResponse =
        data.result?.parts?.[0]?.text ||
        data.result?.message?.parts?.[0]?.text ||
        data.result?.content ||
        "I apologize, but I couldn't process that request.";

      const assistantMessage: Message = {
        role: "assistant",
        content: agentResponse,
        metadata: data.result?.metadata,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Update metrics - check if LLM was used from metadata
      const usedLLM = data.result?.metadata?.used_llm || false;
      const wasCached = data.result?.metadata?.cached || false;
      
      setMetrics((prev) => ({
        ...prev,
        totalRequests: prev.totalRequests + 1,
        llmCalls: usedLLM ? prev.llmCalls + 1 : prev.llmCalls,
        cacheHits: wasCached ? prev.cacheHits + 1 : prev.cacheHits,
        currentCost: prev.currentCost + (data.result?.metadata?.cost || 0),
      }));
    } catch (error) {
      console.error("Error sending message:", error);
      const errorMessage: Message = {
        role: "assistant",
        content:
          "I'm having trouble connecting to the backend. Please make sure the Python backend is running on port 9998.",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
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
        <div className="border-b border-border bg-card/50">
          <div className="container mx-auto px-6 py-4">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <AgentStatus />
              <AgentDashboard metrics={metrics} />
            </div>
          </div>
        </div>

        {/* Chat Area */}
        <main className="flex-1 overflow-auto">
          <div className="container mx-auto px-6 py-6 max-w-4xl">
            {messages.length === 0 ? (
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
            ) : (
              <div className="space-y-4">
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${
                      message.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg p-4 ${
                        message.role === "user"
                          ? "bg-primary text-primary-foreground"
                          : "bg-card border border-border"
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{message.content}</p>
                      {message.metadata && (
                        <div className="mt-2 pt-2 border-t border-border/50 text-xs opacity-70">
                          {message.metadata.intent && (
                            <span className="mr-3">
                              🎯 {message.metadata.intent}
                            </span>
                          )}
                          {message.metadata.model && (
                            <span className="mr-3">
                              🤖 {message.metadata.model}
                            </span>
                          )}
                          {message.metadata.cost !== undefined && (
                            <span>💰 ${message.metadata.cost.toFixed(6)}</span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </main>

        {/* Input Area */}
        <div className="border-t border-border bg-card">
          <div className="container mx-auto px-6 py-4 max-w-4xl">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                disabled={isLoading}
                className="flex-1 px-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
              />
              <button
                onClick={sendMessage}
                disabled={isLoading || !input.trim()}
                className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
                Send
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
