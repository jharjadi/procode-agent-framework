#!/usr/bin/env python3
"""
Demo script showing the console app in action (non-interactive).
This simulates what you would see when using the console app.
"""

import asyncio
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

async def demo_console():
    """Demonstrate the console app functionality."""
    
    # Show welcome
    welcome_text = """
# 🤖 Procode Agent Console

Welcome to the interactive console for the Procode Agent Framework!

## Available Commands:
- Type your message to chat with the agent
- `/help` - Show this help message
- `/clear` - Clear conversation history
- `/history` - Show conversation history
- `/status` - Check agent status
- `/quit` or `/exit` - Exit the console
    """
    console.print(Panel(Markdown(welcome_text), border_style="blue"))
    
    # Check agent health
    agent_url = "http://localhost:9998"
    console.print(f"\n[green]✓ Connected to agent at {agent_url}[/green]\n")
    
    # Simulate conversation
    messages = [
        ("You", "Create a support ticket for login issues"),
        ("You", "Show my account information"),
        ("You", "/status"),
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for i, (role, text) in enumerate(messages, 1):
            console.print(f"\n[bold cyan]{role}:[/bold cyan] {text}")
            
            if text.startswith("/"):
                # Handle command
                if text == "/status":
                    console.print("\n[bold]Checking agent status...[/bold]")
                    console.print(f"[green]✓ Agent is healthy and running at {agent_url}[/green]")
                    console.print(f"[dim]Messages sent: {i}[/dim]")
                    console.print(f"[dim]Conversation turns: {i-1}[/dim]\n")
            else:
                # Send to agent
                console.print("[dim]Sending message...[/dim]")
                
                payload = {
                    "jsonrpc": "2.0",
                    "method": "message/send",
                    "params": {
                        "message": {
                            "role": "user",
                            "parts": [{"kind": "text", "text": text}],
                            "messageId": f"demo-{i}"
                        }
                    },
                    "id": i
                }
                
                try:
                    response = await client.post(agent_url, json=payload)
                    result = response.json()
                    
                    if "result" in result:
                        message = result["result"]
                        if "parts" in message:
                            response_text = message["parts"][0].get("text", "")
                            console.print(f"\n[bold green]Agent:[/bold green]")
                            console.print(Panel(response_text, border_style="green"))
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")
    
    # Show summary
    console.print("\n[yellow]Demo complete! This is what the interactive console looks like.[/yellow]")
    console.print("\n[bold]To use it yourself:[/bold]")
    console.print("  python console_app.py")
    console.print("\nThen you can type your own messages and use commands like:")
    console.print("  /help, /history, /status, /quit")

if __name__ == "__main__":
    try:
        asyncio.run(demo_console())
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted[/yellow]")
