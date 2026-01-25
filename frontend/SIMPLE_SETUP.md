# Simple Frontend Setup (Without CopilotKit)

The CopilotKit integration is complex and requires specific backend configuration. Here's a simpler approach that works immediately with your existing Python backend.

## Quick Alternative: Use the Console App

Your project already has a working console interface! Use it instead:

```bash
# Terminal 1: Start backend
make start

# Terminal 2: Use console app
make console
```

This gives you:
- ✅ Working chat interface
- ✅ Real-time responses
- ✅ Conversation history
- ✅ No frontend complexity

## If You Want a Web UI

I recommend using a simpler approach than CopilotKit:

### Option 1: Streamlit (Easiest - 30 minutes)

Create `streamlit_app.py`:

```python
import streamlit as st
import requests

st.title("Procode Agent 💬")
st.caption("AI Assistant with 98% Cost Savings")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What can I help you with?"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = requests.post(
                "http://localhost:9998/",
                json={
                    "jsonrpc": "2.0",
                    "method": "message/send",
                    "params": {
                        "message": {
                            "role": "user",
                            "parts": [{"kind": "text", "text": prompt}],
                            "messageId": f"msg-{len(st.session_state.messages)}"
                        }
                    },
                    "id": len(st.session_state.messages)
                }
            )
            result = response.json()
            agent_response = result.get("result", {}).get("message", {}).get("parts", [{}])[0].get("text", "Error")
            st.markdown(agent_response)
            st.session_state.messages.append({"role": "assistant", "content": agent_response})
```

Run with:
```bash
pip install streamlit
streamlit run streamlit_app.py
```

### Option 2: Simple HTML/JavaScript (No build required)

Create `simple_frontend.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Procode Agent</title>
    <style>
        body { font-family: Arial; max-width: 800px; margin: 50px auto; }
        #chat { border: 1px solid #ccc; height: 400px; overflow-y: scroll; padding: 10px; }
        .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user { background: #e3f2fd; text-align: right; }
        .agent { background: #f5f5f5; }
        input { width: 80%; padding: 10px; }
        button { padding: 10px 20px; }
    </style>
</head>
<body>
    <h1>Procode Agent 💬</h1>
    <div id="chat"></div>
    <input id="input" placeholder="Type your message..." />
    <button onclick="send()">Send</button>

    <script>
        async function send() {
            const input = document.getElementById('input');
            const message = input.value;
            if (!message) return;

            // Show user message
            addMessage('user', message);
            input.value = '';

            // Call backend
            try {
                const response = await fetch('http://localhost:9998/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        jsonrpc: "2.0",
                        method: "message/send",
                        params: {
                            message: {
                                role: "user",
                                parts: [{ kind: "text", text: message }],
                                messageId: `msg-${Date.now()}`
                            }
                        },
                        id: Date.now()
                    })
                });
                const data = await response.json();
                const agentResponse = data.result?.message?.parts?.[0]?.text || "Error";
                addMessage('agent', agentResponse);
            } catch (error) {
                addMessage('agent', 'Error: Could not connect to backend');
            }
        }

        function addMessage(role, text) {
            const chat = document.getElementById('chat');
            const div = document.createElement('div');
            div.className = `message ${role}`;
            div.textContent = text;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }

        document.getElementById('input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') send();
        });
    </script>
</body>
</html>
```

Open directly in browser - no build needed!

## Recommendation

**Use the existing console app** (`make console`) - it's already working and provides a great user experience without any frontend complexity.

If you need a web UI later, start with Streamlit (Option 1) - it's Python-based and integrates easily with your existing code.

The CopilotKit approach requires more complex setup and isn't necessary for a functional chat interface.
