# Procode Agent Framework (A2A-ready)

A production-style agent framework demonstrating:
- **Streaming responses** for real-time feedback
- **LLM-based intent classification** with multi-provider support
- **Conversation memory** for multi-turn dialogues
- **Real tool integration** with GitHub Issues API
- Principal agent routing
- Task agents (tickets, account, payments)
- Hybrid tools (mocked/real)
- Input/output guardrails
- Comprehensive test coverage

## Setup

### 1. Install Dependencies

```bash
cd samples/python/agents/procode_framework
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### 2. Configure API Key (Optional)

For LLM-based intent classification, set one of the following API keys:

**Anthropic (Claude) - Recommended:**
```bash
export ANTHROPIC_API_KEY="your-anthropic-key"
```

**OpenAI (GPT):**
```bash
export OPENAI_API_KEY="your-openai-key"
```

**Google (Gemini):**
```bash
export GOOGLE_API_KEY="your-google-key"
```

The agent will automatically detect and use the first available provider in this order:
1. Anthropic (Claude 3.5 Sonnet)
2. OpenAI (GPT-4o-mini)
3. Google (Gemini 2.0 Flash)

You can also specify a provider explicitly:
```bash
export LLM_PROVIDER="anthropic"  # or "openai" or "google"
```

Without any API key, the agent will automatically fall back to deterministic keyword matching.

### 3. Configure LLM Usage (Optional)

Control whether to use LLM for intent classification:

```bash
# Use LLM (default if any API key is set)
export USE_LLM_INTENT=true

# Use deterministic matching only
export USE_LLM_INTENT=false
```

### 4. Configure GitHub Integration (Optional - Step 5)

For real ticket creation via GitHub Issues:

```bash
# Set your GitHub personal access token
export GITHUB_TOKEN="ghp_your_token_here"

# Set the repository (format: owner/repo)
export GITHUB_REPO="your-username/your-repo"

# Enable real tools (default: false, uses mocked tools)
export USE_REAL_TOOLS=true
```

**To create a GitHub token:**
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `repo` scope (for private repos) or `public_repo` (for public repos)
3. Copy the token and set it as `GITHUB_TOKEN`

**Note**: Without these settings, the agent uses mocked tools (safe for testing).

## Run the Agent

```bash
source venv/bin/activate
python -m procode_framework
# or
python __main__.py
```

The agent will be available at: http://localhost:9998/

## Interactive Console App 🎨

For easier testing and interaction, use the **console app** instead of curl:

```bash
# Terminal 1: Start the agent
source venv/bin/activate
python __main__.py

# Terminal 2: Run the console app
source venv/bin/activate
python console_app.py
```

### Console Features

- 🎨 **Beautiful UI** with colors and formatting
- 💬 **Interactive chat** with natural conversation flow
- 📝 **History tracking** - view past conversations
- 🔍 **Health checks** - monitor agent status
- ⌨️ **Built-in commands** - `/help`, `/history`, `/status`, `/clear`, `/quit`

### Example Usage

```
You: Create a support ticket for login issues
Agent: Ticket processed (mocked). Ticket ID: MOCK-001

You: /history
Conversation History:
You (1): Create a support ticket for login issues
Agent (1): Ticket processed (mocked). Ticket ID: MOCK-001

You: /status
✓ Agent is healthy and running at http://localhost:9998
```

See [`docs/CONSOLE_APP.md`](docs/CONSOLE_APP.md) for full documentation.

## Run the Tests

### Unit Tests (Default)

```bash
source venv/bin/activate
python tests.py
```

**Note**:
- Unit tests use mocked tools and work without any credentials
- LLM tests are skipped if no API key is available
- Integration tests are skipped by default

### Integration Tests (Optional)

To run integration tests with real GitHub API:

```bash
# Set GitHub credentials
export GITHUB_TOKEN="your-token"
export GITHUB_REPO="owner/repo"

# Enable integration tests
export RUN_INTEGRATION_TESTS=true

# Run tests
python tests.py
```

**Warning**: Integration tests will create real GitHub issues in your repository!

## Example Requests

### Using JSON-RPC (A2A Protocol)

#### Ticket request (keyword-based)
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
        "messageId": "msg-001"
      }
    },
    "id": 1
  }'
```

#### Ticket request (natural language - requires API key)
```bash
curl -X POST http://localhost:9998/ \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "I need help with my order, something went wrong"}],
        "messageId": "msg-002"
      }
    },
    "id": 2
  }'
```

#### Account request (natural language)
```bash
curl -X POST http://localhost:9998/ \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "Can you show me my profile information?"}],
        "messageId": "msg-003"
      }
    },
    "id": 3
  }'
```

#### Payment request (should be refused)
```bash
curl -X POST http://localhost:9998/ \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "I want to make a payment"}],
        "messageId": "msg-004"
      }
    },
    "id": 4
  }'
```

### Using Streaming Endpoint (Step 7)

The agent supports **Server-Sent Events (SSE)** for real-time streaming responses:

#### Streaming ticket creation
```bash
curl -N -X POST http://localhost:9998/stream \
  -H 'Content-Type: application/json' \
  -d '{
    "message": {
      "role": "user",
      "parts": [{"kind": "text", "text": "Create a support ticket for login issue"}]
    }
  }'
```

#### Streaming with natural language
```bash
curl -N -X POST http://localhost:9998/stream \
  -H 'Content-Type: application/json' \
  -d '{
    "message": {
      "role": "user",
      "parts": [{"kind": "text", "text": "I need help with my account settings"}]
    }
  }'
```

**Note**: The `-N` flag disables buffering for real-time streaming output.

#### Expected Streaming Output

```
data: {"text": "🤔 Analyzing your request...\n"}
data: {"text": "📋 Using keyword matching...\n"}
data: {"text": "✓ Intent identified: tickets\n"}
data: {"text": "\n🔧 Executing tickets task...\n"}
data: {"text": "\n📋 Result:\n"}
data: {"text": "Ticket created successfully! "}
data: {"text": "Issue #123: https://github.com/..."}
```

### Streaming Benefits

- **Real-time Feedback**: See progress as the agent works
- **Reduced Perceived Latency**: Users see immediate response
- **Progress Tracking**: Visual indicators for each step
- **Better UX**: Especially for long-running operations

## Architecture

### Intent Classification (Step 4 Enhancement)

The agent uses a hybrid approach for intent classification:

1. **LLM-based Classification** (when `GOOGLE_API_KEY` is set):
   - Uses Google Gemini for natural language understanding
   - Handles ambiguous and conversational inputs
   - Temperature set to 0.0 for deterministic results
   - Few-shot prompting for accurate classification

2. **Deterministic Fallback**:
   - Keyword-based matching as backup
   - Always available (no API key required)
   - Fast and reliable for simple inputs
   - Automatically used if LLM fails

### Components

- **Principal Agent Router** (`agent_router.py`): Routes requests to task agents based on classified intent
- **Intent Classifier** (`intent_classifier.py`): LLM-based classification with deterministic fallback
- **Task Agents**:
  - `task_tickets.py`: Handles support ticket operations
  - `task_account.py`: Manages account-related queries
  - `task_payments.py`: Refuses payment operations (stubbed for safety)
- **Tools** (`tools.py`): Mocked tool implementations
- **Guardrails** (`guardrails.py`): Input/output validation
- **Tests** (`tests.py`): Comprehensive test coverage including natural language inputs

## Conversation Memory (Step 6)

The agent now supports **multi-turn conversations** with context awareness:

- **Automatic History Tracking**: Stores user and agent messages
- **Context Window Management**: Keeps last 10 messages by default (configurable)
- **Follow-up Questions**: Agent can reference previous messages
- **Conversation ID Tracking**: Separate conversations maintained independently
- **Automatic Cleanup**: Old conversations removed after 24 hours

### Configuration

```bash
# Set conversation window size (default: 10 messages)
export CONVERSATION_WINDOW_SIZE=20
```

### Example Multi-Turn Conversation

```bash
# Turn 1: Create a ticket
curl -X POST http://localhost:9998/ -H 'Content-Type: application/json' -d '{
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [{"kind": "text", "text": "I need to create a support ticket"}],
      "messageId": "conv-123-msg1"
    }
  },
  "id": 1
}'

# Turn 2: Follow-up question (agent remembers context)
curl -X POST http://localhost:9998/ -H 'Content-Type: application/json' -d '{
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [{"kind": "text", "text": "What is the status?"}],
      "messageId": "conv-123-msg2"
    }
  },
  "id": 2
}'
```

The agent will recognize "What is the status?" refers to the ticket from the previous message.

## Streaming Responses (Step 7)

The agent supports **real-time streaming** for improved user experience:

### Features

- **Server-Sent Events (SSE)**: Standard streaming protocol
- **Progress Indicators**: Visual feedback for each step
- **Token-by-Token Streaming**: Responses stream as they're generated
- **Tool Progress**: Real-time updates during tool execution
- **Error Handling**: Graceful error streaming
- **Backward Compatible**: Non-streaming endpoints still work

### Testing Streaming

Run streaming tests:
```bash
source venv/bin/activate
python test_streaming.py
```

Or run specific streaming tests:
```bash
pytest test_streaming.py::TestStreamingHandler -v
pytest test_streaming.py::TestAgentRouterStreaming -v
```

## Features

- ✅ **Streaming Responses**: Real-time SSE streaming with progress indicators
- ✅ **A2A Protocol Compatible**: Full Agent-to-Agent protocol support
- ✅ **Multi-Provider LLM**: Supports Anthropic, OpenAI, and Google
- ✅ **Conversation Memory**: Multi-turn dialogues with context awareness
- ✅ **Natural Language Understanding**: Handles conversational inputs
- ✅ **Real Tool Integration**: GitHub Issues API with retry logic
- ✅ **Hybrid Tools**: Mocked tools for testing, real tools for production
- ✅ **Deterministic Fallback**: Works without any API keys
- ✅ **Input/Output Validation**: Guardrails for safety
- ✅ **Comprehensive Tests**: Unit tests + optional integration tests
- ✅ **Production-Ready**: Error handling, retries, rate limiting
- ✅ **Graceful Degradation**: Falls back to mocked tools if credentials missing
