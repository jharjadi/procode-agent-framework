import { NextRequest } from "next/server";
import {
  CopilotRuntime,
  OpenAIAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";

/**
 * CopilotKit Runtime Endpoint
 *
 * This creates a custom adapter that forwards requests to our Python backend
 */

// For API routes, we can use regular env vars (not NEXT_PUBLIC_)
// because API routes run on the server side
const BACKEND_URL = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_AGENT_URL || "http://agent:9998";
const DEMO_API_KEY = process.env.DEMO_API_KEY || "";

console.log("Backend URL:", BACKEND_URL);
console.log("API Key configured:", !!DEMO_API_KEY);

// Custom service adapter for our Python backend
const customAdapter = new OpenAIAdapter({
  model: "gpt-4", // This is just for CopilotKit's internal tracking
}) as any;

// Override the adapter's execute method to call our backend
const originalExecute = customAdapter.execute?.bind(customAdapter);
customAdapter.execute = async function(params: any) {
  try {
    // Extract the user's message from CopilotKit format
    const messages = params.messages || [];
    const lastMessage = messages[messages.length - 1];
    const userMessage = lastMessage?.content || "";

    // Format for A2A protocol
    const a2aRequest = {
      jsonrpc: "2.0",
      method: "message/send",
      params: {
        message: {
          role: "user",
          parts: [
            {
              kind: "text",
              text: userMessage,
            },
          ],
          messageId: `msg-${Date.now()}`,
        },
      },
      id: Date.now(),
    };

    // Call Python backend
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    
    // Add API key if configured (for production deployments)
    if (DEMO_API_KEY) {
      headers["X-API-Key"] = DEMO_API_KEY;
    }
    
    const response = await fetch(BACKEND_URL, {
      method: "POST",
      headers,
      body: JSON.stringify(a2aRequest),
    });

    if (!response.ok) {
      throw new Error(`Backend responded with ${response.status}`);
    }

    const data = await response.json();
    
    // Extract response from A2A format
    const agentResponse = data.result?.parts?.[0]?.text ||
                         data.result?.message?.parts?.[0]?.text ||
                         data.result?.content ||
                         "I apologize, but I couldn't process that request.";

    // Return in OpenAI-compatible format for CopilotKit
    return {
      choices: [
        {
          message: {
            role: "assistant",
            content: agentResponse,
          },
          finish_reason: "stop",
        },
      ],
      usage: {
        prompt_tokens: 0,
        completion_tokens: 0,
        total_tokens: 0,
      },
    };
  } catch (error) {
    console.error("Error calling backend:", error);
    // Return error message in OpenAI format
    return {
      choices: [
        {
          message: {
            role: "assistant",
            content: "I'm having trouble connecting to the backend. Please make sure the Python backend is running on port 9998.",
          },
          finish_reason: "stop",
        },
      ],
    };
  }
};

const runtime = new CopilotRuntime();

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: customAdapter,
    endpoint: "/api/copilot",
  });

  return handleRequest(req);
};
