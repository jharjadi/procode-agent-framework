import { NextRequest, NextResponse } from "next/server";

/**
 * CopilotKit API Route
 *
 * Forwards chat requests to your Python backend via A2A protocol
 */

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:9998";

// POST /api/copilot - Handle chat messages
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Extract message from CopilotKit format
    const userMessage = body.message || body.text || body.messages?.[body.messages.length - 1]?.content || "";
    
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

    // Forward to Python backend
    const response = await fetch(BACKEND_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(a2aRequest),
    });

    if (!response.ok) {
      throw new Error(`Backend responded with ${response.status}`);
    }

    const data = await response.json();
    
    // Extract response from A2A format
    const agentResponse = data.result?.message?.parts?.[0]?.text ||
                         data.result?.content ||
                         "I apologize, but I couldn't process that request.";

    // Return in CopilotKit format
    return NextResponse.json({
      message: agentResponse,
      metadata: {
        intent: data.result?.metadata?.intent,
        model: data.result?.metadata?.model,
        cost: data.result?.metadata?.cost,
      },
    });
  } catch (error) {
    console.error("Error in copilot route:", error);
    return NextResponse.json(
      {
        error: "Failed to communicate with agent",
        message: "I'm having trouble connecting to the backend. Please make sure the Python backend is running on port 9998.",
      },
      { status: 500 }
    );
  }
}

// Handle OPTIONS for CORS
export async function OPTIONS(request: NextRequest) {
  return new NextResponse(null, {
    status: 200,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    },
  });
}
