import streamlit as st
import requests

st.set_page_config(page_title="My Chatbot", page_icon="💬")
st.title("Participant Chatbot")

FLASK_URL = "http://127.0.0.1:5000/chat"

# 1. Sidebar for Participant Configuration
with st.sidebar:
    st.header("Session Setup")
    
    # number_input strictly forces numerical entries. value=None leaves it blank initially.
    p_id = st.number_input("Participant ID", min_value=1, step=1, value=None, placeholder="e.g., 1")
    
    # index=None forces the dropdown to start unselected
    p_topic = st.selectbox(
        "Topic", 
        ["defense", "migration", "climate"], 
        index=None,
        placeholder="Select a topic..."
    )

# 2. Lock the chat if ID or Topic are missing (since they start as None)
if p_id is None or p_topic is None:
    st.warning("Please enter a Participant ID and select a Topic in the sidebar to begin.")
    st.stop() # Halts execution until fields are filled

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Type your message here..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    history_for_api = st.session_state.messages.copy()
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    try:
        # p_id is now a number, but JSON handles it perfectly
        payload = {
            "message": prompt, 
            "history": history_for_api,
            "participant_id": p_id,
            "participant_topic": p_topic
        }
        
        response = requests.post(FLASK_URL, json=payload)
        
        if response.status_code == 200:
            reply = response.json().get("reply")
            with st.chat_message("assistant"):
                st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
        else:
            st.error(f"Backend Error: {response.json().get('error')}")
            
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the Flask backend. Make sure app.py is running!")