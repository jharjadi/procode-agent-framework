# Console App - Interactive Testing Interface

The console app provides an interactive command-line interface for testing the Procode Agent Framework without needing curl or writing test scripts.

## Features

- 🎨 **Beautiful UI** - Rich terminal interface with colors and formatting
- 💬 **Interactive Chat** - Natural conversation flow with the agent
- 📝 **History Tracking** - View and manage conversation history
- 🔍 **Health Checks** - Monitor agent status
- ⌨️ **Command System** - Built-in commands for common operations

## Quick Start

### 1. Start the Agent Server

In one terminal:
```bash
cd samples/python/agents/procode_framework
source venv/bin/activate
python __main__.py
```

### 2. Run the Console App

In another terminal:
```bash
cd samples/python/agents/procode_framework
source venv/bin/activate
python console_app.py
```

## Usage

### Basic Chat

Simply type your message and press Enter:

```
You: Create a support ticket for login issues
Agent: Ticket processed (mocked). Ticket ID: MOCK-001
```

### Available Commands

| Command            | Description                              |
| ------------------ | ---------------------------------------- |
| `/help`            | Show help message with all commands      |
| `/clear`           | Clear conversation history               |
| `/history`         | Display full conversation history        |
| `/status`          | Check agent health and connection status |
| `/quit` or `/exit` | Exit the console app                     |

### Example Queries

**Ticket Operations:**
```
Create a support ticket for login issues
List all open tickets
What's the status of ticket #123?
```

**Account Operations:**
```
Show my account information
Get my profile details
Update my account settings
```

**Payment Operations:**
```
Make a payment
Check my billing information
Update payment method
```

## Configuration

### Custom Agent URL

Set via environment variable:
```bash
export AGENT_URL=http://localhost:8000
python console_app.py
```

Or pass as command-line argument:
```bash
python console_app.py http://localhost:8000
```

### Default Settings

- **Agent URL:** `http://localhost:9998`
- **Timeout:** 30 seconds
- **Auto-reconnect:** Yes

## Features in Detail

### Conversation History

The console app maintains a conversation history for the current session:

```
You: /history

Conversation History:
You (1): Create a ticket
Agent (1): Ticket processed (mocked). Ticket ID: MOCK-001
You (2): What's the status?
Agent (2): To check ticket status, please provide the ticket ID...
```

### Health Monitoring

Check agent status at any time:

```
You: /status

Checking agent status...
✓ Agent is healthy and running at http://localhost:9998
Messages sent: 5
Conversation turns: 2
```

### Error Handling

The console app gracefully handles:
- Connection failures
- Timeouts
- Invalid responses
- Network errors

## Troubleshooting

### Agent Not Running

If you see:
```
⚠ Warning: Agent doesn't appear to be running at http://localhost:9998
Start it with: python __main__.py
```

**Solution:** Start the agent server in another terminal.

### Connection Refused

If you see:
```
✗ Cannot connect to agent at http://localhost:9998
Make sure the agent is running with: python __main__.py
```

**Solution:** 
1. Check if the agent is running
2. Verify the URL is correct
3. Check for port conflicts

### Timeout Errors

If requests timeout:
1. Check network connectivity
2. Verify agent is responsive
3. Try increasing timeout in code if needed

## Development

### Adding New Commands

Edit `console_app.py` and add to the command handler:

```python
elif command == "/mycommand":
    # Your command logic here
    console.print("[green]Command executed[/green]")
```

### Customizing UI

The console app uses the `rich` library for formatting. Customize colors and styles in the display methods.

## Tips

1. **Use Tab Completion** - Some terminals support tab completion for commands
2. **Ctrl+C** - Interrupts current operation without exiting
3. **Ctrl+D** - Alternative way to exit
4. **Arrow Keys** - Navigate command history (terminal-dependent)

## Integration with Testing

The console app is perfect for:
- Manual testing during development
- Demonstrating agent capabilities
- Debugging conversation flows
- Validating new features

For automated testing, use the test suite in `tests/`.
