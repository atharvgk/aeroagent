import streamlit as st
import time
from agent_llm import AgentLLM
import pandas as pd

# Page Config
st.set_page_config(page_title="Skylark SkyOps AI", page_icon="🚁", layout="wide")

# Custom CSS for "Cyberpunk/SaaS" aesthetic
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .stChatMessage {
        background-color: #262730;
        border-radius: 10px;
        border: 1px solid #4B4B4B;
    }
    .stButton>button {
        background-color: #FF4B4B;
        color: white;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Initial greeting
    st.session_state.messages.append({"role": "assistant", "content": "Hello, I am **SkyOps AI**. How can I assist with your drone operations today?"})

# Initialize Agent
# We pass the local API URL. OpenRouter Key is loaded from .env by AgentLLM
if "agent" not in st.session_state:
    st.session_state.agent = AgentLLM(api_url="http://127.0.0.1:8000")

# --- Chat Interface ---
st.title("SkyOps AI Coordinator")

# Display History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Assign P001 to PRJ001..."):
    # Add User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing operational data..."):
            try:
                response = st.session_state.agent.process_message(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Agent Error: {e}")
