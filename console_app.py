#!/usr/bin/env python3
"""
Interactive Console App for Procode Agent Framework

This console app provides an interactive interface for testing the agent
without needing to use curl or write test scripts.
"""

import asyncio
import sys
import os
from typing import Optional
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table
from rich import print as rprint

console = Console()


class AgentConsoleClient:
    """Interactive console client for the Procode Agent."""
    
    def __init__(self, agent_url: str = "http://localhost:9998"):
        """
        Initialize the console client.
        
        Args:
            agent_url: URL of the agent server
        """
        self.agent_url = agent_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
        self.conversation_history = []
        self.message_count = 0
    
    async def send_message(self, text: str) -> Optional[str]:
        """
        Send a message to the agent.
        
        Args:
            text: Message text to send
            
        Returns:
            Response text from agent, or None if error
        """
        try:
            # Create JSON-RPC request
            payload = {
                "jsonrpc": "2.0",
                "method": "message/send",
                "params": {
                    "message": {
                        "role": "user",
                        "parts": [{"kind": "text", "text": text}],
                        "messageId": f"msg-{self.message_count}"
                    }
                },
                "id": self.message_count
            }
            
            self.message_count += 1
            
            # Send request
            response = await self.client.post(self.agent_url, json=payload)
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            if "error" in result:
                error = result["error"]
                console.print(f"[red]Error: {error.get('message', 'Unknown error')}[/red]")
                return None
            
            if "result" in result:
                # Extract text from response
                response_msg = result["result"]
                if isinstance(response_msg, dict) and "parts" in response_msg:
                    texts = []
                    for part in response_msg["parts"]:
                        if isinstance(part, dict):
                            if "text" in part:
                                texts.append(part["text"])
                            elif "root" in part and "text" in part["root"]:
                                texts.append(part["root"]["text"])
                    return " ".join(texts) if texts else str(response_msg)
                return str(response_msg)
            
            return None
        
        except httpx.ConnectError:
            console.print(f"[red]✗ Cannot connect to agent at {self.agent_url}[/red]")
            console.print("[yellow]Make sure the agent is running with: python __main__.py[/yellow]")
            return None
        except httpx.TimeoutException:
            console.print("[red]✗ Request timed out[/red]")
            return None
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            return None
    
    async def check_health(self) -> bool:
        """
        Check if the agent is healthy.
        
        Returns:
            True if agent is healthy, False otherwise
        """
        try:
            response = await self.client.get(f"{self.agent_url}/health", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    def display_welcome(self):
        """Display welcome message."""
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

## Example Queries:
- "Create a support ticket for login issues"
- "Show my account information"
- "List all open tickets"
- "What's the status of ticket #123?"

The agent supports tickets, account, and payment operations.
        """
        console.print(Panel(Markdown(welcome_text), border_style="blue"))
    
    def display_help(self):
        """Display help information."""
        table = Table(title="Available Commands", show_header=True, header_style="bold magenta")
        table.add_column("Command", style="cyan", width=20)
        table.add_column("Description", style="white")
        
        table.add_row("/help", "Show this help message")
        table.add_row("/clear", "Clear conversation history")
        table.add_row("/history", "Show conversation history")
        table.add_row("/status", "Check agent health status")
        table.add_row("/quit, /exit", "Exit the console")
        table.add_row("<message>", "Send a message to the agent")
        
        console.print(table)
    
    def display_history(self):
        """Display conversation history."""
        if not self.conversation_history:
            console.print("[yellow]No conversation history yet.[/yellow]")
            return
        
        console.print("\n[bold]Conversation History:[/bold]")
        for i, (role, text) in enumerate(self.conversation_history, 1):
            if role == "user":
                console.print(f"\n[cyan]You ({i}):[/cyan] {text}")
            else:
                console.print(f"[green]Agent ({i}):[/green] {text}")
        console.print()
    
    async def display_status(self):
        """Display agent status."""
        console.print("\n[bold]Checking agent status...[/bold]")
        
        is_healthy = await self.check_health()
        
        if is_healthy:
            console.print(f"[green]✓ Agent is healthy and running at {self.agent_url}[/green]")
        else:
            console.print(f"[red]✗ Agent is not responding at {self.agent_url}[/red]")
            console.print("[yellow]Start the agent with: python __main__.py[/yellow]")
        
        console.print(f"[dim]Messages sent: {self.message_count}[/dim]")
        console.print(f"[dim]Conversation turns: {len(self.conversation_history) // 2}[/dim]\n")
    
    async def run(self):
        """Run the interactive console."""
        self.display_welcome()
        
        # Check if agent is running
        if not await self.check_health():
            console.print(f"[yellow]⚠ Warning: Agent doesn't appear to be running at {self.agent_url}[/yellow]")
            console.print("[yellow]Start it with: python __main__.py[/yellow]")
            should_continue = Prompt.ask("\nContinue anyway?", choices=["y", "n"], default="n")
            if should_continue.lower() != "y":
                return
        else:
            console.print(f"[green]✓ Connected to agent at {self.agent_url}[/green]\n")
        
        # Main interaction loop
        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith("/"):
                    command = user_input.lower()
                    
                    if command in ["/quit", "/exit"]:
                        console.print("\n[yellow]Goodbye! 👋[/yellow]")
                        break
                    
                    elif command == "/help":
                        self.display_help()
                    
                    elif command == "/clear":
                        self.conversation_history.clear()
                        console.print("[green]✓ Conversation history cleared[/green]")
                    
                    elif command == "/history":
                        self.display_history()
                    
                    elif command == "/status":
                        await self.display_status()
                    
                    else:
                        console.print(f"[red]Unknown command: {user_input}[/red]")
                        console.print("[dim]Type /help for available commands[/dim]")
                    
                    continue
                
                # Send message to agent
                console.print("[dim]Sending message...[/dim]")
                response = await self.send_message(user_input)
                
                if response:
                    # Store in history
                    self.conversation_history.append(("user", user_input))
                    self.conversation_history.append(("agent", response))
                    
                    # Display response
                    console.print(f"\n[bold green]Agent:[/bold green]")
                    console.print(Panel(response, border_style="green"))
                else:
                    console.print("[red]Failed to get response from agent[/red]")
            
            except KeyboardInterrupt:
                console.print("\n\n[yellow]Interrupted. Type /quit to exit.[/yellow]")
                continue
            except EOFError:
                console.print("\n[yellow]Goodbye! 👋[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")


async def main():
    """Main entry point."""
    # Get agent URL from environment or use default
    agent_url = os.getenv("AGENT_URL", "http://localhost:9998")
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help"]:
            print("Usage: python console_app.py [AGENT_URL]")
            print(f"Default URL: {agent_url}")
            print("\nEnvironment variables:")
            print("  AGENT_URL - Set the agent URL")
            return
        agent_url = sys.argv[1]
    
    # Create and run client
    client = AgentConsoleClient(agent_url)
    try:
        await client.run()
    finally:
        await client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye! 👋")
