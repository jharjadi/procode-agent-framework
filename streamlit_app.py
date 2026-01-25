"""
Streamlit Web UI for Procode Agent Framework
Simple, working alternative to the complex CopilotKit setup
"""

import streamlit as st
import requests
import json
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Procode Agent",
    page_icon="💬",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .cost-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        display: inline-block;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "total_cost" not in st.session_state:
    st.session_state.total_cost = 0.0
if "request_count" not in st.session_state:
    st.session_state.request_count = 0

# Sidebar
with st.sidebar:
    st.title("💰 Cost Optimization")
    st.markdown("### Session Stats")
    st.metric("Total Requests", st.session_state.request_count)
    st.metric("Session Cost", f"${st.session_state.total_cost:.4f}")
    st.metric("Cost Savings", "98%", delta="vs. baseline")
    
    st.markdown("---")
    st.markdown("### About")
    st.info("""
    This agent uses a multi-LLM strategy:
    - 🟢 Deterministic (Free)
    - 🔵 Cached (Free)
    - 🟡 Haiku ($0.0001)
    - 🔴 Sonnet ($0.001)
    
    Most requests are handled for free!
    """)
    
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.total_cost = 0.0
        st.session_state.request_count = 0
        st.rerun()

# Main content
st.title("Procode Agent 💬")
st.caption("AI Assistant with 98% Cost Savings")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "metadata" in message and message["metadata"]:
            meta = message["metadata"]
            if "intent" in meta:
                st.caption(f"🎯 Intent: {meta['intent']}")
            if "model" in meta:
                model_emoji = {
                    "deterministic": "🟢",
                    "cached": "🔵",
                    "haiku": "🟡",
                    "sonnet": "🔴"
                }.get(meta["model"], "⚪")
                st.caption(f"{model_emoji} Model: {meta['model']}")

# Chat input
if prompt := st.chat_input("What can I help you with?"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt, "metadata": {}})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call backend
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            try:
                # Prepare request
                request_data = {
                    "jsonrpc": "2.0",
                    "method": "message/send",
                    "params": {
                        "message": {
                            "role": "user",
                            "parts": [{"kind": "text", "text": prompt}],
                            "messageId": f"msg-{datetime.now().timestamp()}"
                        }
                    },
                    "id": st.session_state.request_count + 1
                }
                
                # Call backend
                response = requests.post(
                    "http://localhost:9998/",
                    json=request_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Extract response
                    agent_response = "I apologize, but I couldn't process that request."
                    metadata = {}
                    
                    if "result" in result:
                        result_data = result["result"]
                        if isinstance(result_data, dict):
                            # The response format is: result.parts[0].text
                            if "parts" in result_data:
                                parts = result_data["parts"]
                                if parts and len(parts) > 0:
                                    if isinstance(parts[0], dict):
                                        agent_response = parts[0].get("text", agent_response)
                            # Fallback: check for message.parts
                            elif "message" in result_data:
                                msg = result_data["message"]
                                if isinstance(msg, dict) and "parts" in msg:
                                    parts = msg["parts"]
                                    if parts and len(parts) > 0:
                                        agent_response = parts[0].get("text", agent_response)
                            # Fallback: direct content
                            elif "content" in result_data:
                                agent_response = result_data["content"]
                            
                            # Extract metadata (if available)
                            if "metadata" in result_data:
                                metadata = result_data["metadata"]
                    
                    # Display response
                    st.markdown(agent_response)
                    
                    # Display metadata
                    if metadata:
                        if "intent" in metadata:
                            st.caption(f"🎯 Intent: {metadata['intent']}")
                        if "model" in metadata:
                            model_emoji = {
                                "deterministic": "🟢",
                                "cached": "🔵",
                                "haiku": "🟡",
                                "sonnet": "🔴"
                            }.get(metadata.get("model"), "⚪")
                            st.caption(f"{model_emoji} Model: {metadata['model']}")
                        if "cost" in metadata:
                            st.caption(f"💰 Cost: ${metadata['cost']:.6f}")
                            st.session_state.total_cost += metadata["cost"]
                    
                    # Update session
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": agent_response,
                        "metadata": metadata
                    })
                    st.session_state.request_count += 1
                    
                else:
                    error_msg = f"❌ Backend error: {response.status_code}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "metadata": {}
                    })
                    
            except requests.exceptions.ConnectionError:
                error_msg = "❌ Cannot connect to backend. Make sure the Python backend is running on port 9998.\n\nRun: `make start` or `python __main__.py`"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "metadata": {}
                })
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "metadata": {}
                })

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**Features:**")
    st.markdown("✅ Real-time chat")
with col2:
    st.markdown("**Cost Optimized:**")
    st.markdown("✅ 98% savings")
with col3:
    st.markdown("**Backend:**")
    if st.button("Check Status"):
        try:
            response = requests.get("http://localhost:9998/", timeout=2)
            st.success("✅ Backend is running")
        except:
            st.error("❌ Backend not running")
