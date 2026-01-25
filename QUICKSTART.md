# Procode Agent Framework - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the framework
pip install -e .
```

### 2. Start the Agent

```bash
python __main__.py
```

The agent will start on `http://localhost:9998`

### 3. Test with Console App

In a new terminal:

```bash
source venv/bin/activate
python console_app.py
```

When you see the warning, type `y` to continue. Then try:
- `Create a support ticket for login issues`
- `/history` - View conversation
- `/status` - Check agent health
- `/quit` - Exit

### 4. Or Test with curl

```bash
curl -X POST http://localhost:9998/ \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "create ticket"}],
        "messageId": "test-1"
      }
    },
    "id": 1
  }'
```

## 🎯 What Can It Do?

### Ticket Operations
- "Create a support ticket"
- "List all open tickets"
- "Show ticket status"

### Account Operations
- "Show my account information"
- "Get my profile"

### Payment Operations
- "Make a payment" (will be refused - stubbed for safety)

## 🔧 Configuration (Optional)

### Add LLM for Natural Language

```bash
# Use one of these:
export ANTHROPIC_API_KEY="your-key"  # Recommended
export OPENAI_API_KEY="your-key"
export GOOGLE_API_KEY="your-key"
```

Without an API key, the agent uses keyword matching (works fine for testing).

### Enable Real GitHub Integration

```bash
export USE_REAL_TOOLS=true
export GITHUB_TOKEN="ghp_your_token"
export GITHUB_REPO="owner/repo"
```

Without these, the agent uses mocked tools (safe for testing).

## 📚 Learn More

- **[README.md](README.md)** - Full documentation
- **[docs/CONSOLE_APP.md](docs/CONSOLE_APP.md)** - Console app guide
- **[docs/STRUCTURE.md](docs/STRUCTURE.md)** - Project structure
- **[docs/DEVELOPMENT_HISTORY.md](docs/DEVELOPMENT_HISTORY.md)** - Development context
- **[docs/CONTEXT_FOR_AI.md](docs/CONTEXT_FOR_AI.md)** - AI assistant context

## 🧪 Run Tests

```bash
# Quick test
python test_console.py

# Full test suite
python tests/tests.py

# Demo
python demo_console.py
```

## 🐛 Troubleshooting

### "Agent doesn't appear to be running"
- This is a false warning from the console app
- Type `y` to continue - the agent works fine
- The warning appears because there's no `/health` endpoint

### "ModuleNotFoundError"
- Make sure you ran `pip install -e .`
- Make sure virtual environment is activated

### "Port 9998 already in use"
- Kill existing process: `lsof -ti:9998 | xargs kill -9`
- Or use a different port in `__main__.py`

## 🎨 Features

✅ A2A Protocol Support
✅ LLM Intent Classification (multi-provider)
✅ Streaming Responses (SSE)
✅ Conversation Memory
✅ Agent-to-Agent Communication
✅ Interactive Console App
✅ Comprehensive Tests
✅ Clean Architecture

## 📝 Next Steps

1. Try the interactive console: `python console_app.py`
2. Read the full README: `README.md`
3. Explore the code structure: `docs/STRUCTURE.md`
4. Run the tests: `python tests/tests.py`
5. Add your own features!

## 💡 Tips

- Use the console app for interactive testing (much better than curl)
- Check `docs/CONTEXT_FOR_AI.md` if you're using an AI assistant
- The agent works without any API keys (uses keyword matching)
- All tools are mocked by default (safe for testing)

## 🤝 Contributing

See [DEVELOPMENT_HISTORY.md](docs/DEVELOPMENT_HISTORY.md) for:
- Development timeline
- Architecture decisions
- Known issues
- Roadmap

---

**Ready to build intelligent agents? Start with `python console_app.py`!** 🚀
