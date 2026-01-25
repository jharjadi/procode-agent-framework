import { NextResponse } from "next/server";

/**
 * CopilotKit Info Endpoint
 * Required by CopilotKit to discover available agents
 */

export async function GET() {
  return NextResponse.json({
    agents: [
      {
        name: "default",
        description: "Procode AI Agent with 98% cost savings",
        capabilities: [
          "Support ticket creation",
          "Account management",
          "General assistance",
        ],
      },
    ],
  });
}
