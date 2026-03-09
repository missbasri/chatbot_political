import streamlit as st
import requests

st.set_page_config(page_title="My Chatbot", page_icon="💬", layout="wide")
st.title("Participant Chatbot")

FLASK_URL = "http://127.0.0.1:5000/chat"

# --- Topic Configuration ---
TOPICS_ORDER = ["defense", "migration", "climate"]
TOPIC_NAMES = {
    "defense": "EU Security and Defense",
    "migration": "EU Migration Policy",
    "climate": "EU Climate Policy"
}

TOPIC_QUESTIONS = {
    "defense": [
        "1. The EU should move toward a common European army.",
        "2. Germany should continue providing military support to Ukraine.",
        "3. Ukraine should become a member of the European Union."
    ],
    "migration": [
        "1. Asylum seekers must submit their application at the EU's external borders and await the outcome there.",
        "2. Ukrainian refugees should no longer benefit from a special status.",
        "3. Permanent border controls should be reinstated between all EU member states."
    ],
    "climate": [
        "1. The EU should continue to recognize nuclear energy as a sustainable energy source.",
        "2. Companies should pay more for their CO2 emissions.",
        "3. Vehicles with combustion engines should continue to be registered in the EU even after 2035."
    ]
}

# --- Session State Management ---
if "topic_index" not in st.session_state:
    st.session_state.topic_index = 0
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "participant_id" not in st.session_state:
    st.session_state.participant_id = None

# --- 1. Top Navigation Bar (Topic Progress) ---
st.markdown("### 📌 Discussion Progress")
cols = st.columns(3)
for i, topic in enumerate(TOPICS_ORDER):
    if i == st.session_state.topic_index:
        cols[i].success(f"**🟢 {TOPIC_NAMES[topic]}**")
    elif i < st.session_state.topic_index:
        cols[i].info(f"✔️ {TOPIC_NAMES[topic]}")
    else:
        cols[i].error(f"🔒 {TOPIC_NAMES[topic]}")
st.divider()

# Stop execution if all topics are completed
if st.session_state.topic_index >= len(TOPICS_ORDER):
    st.balloons()
    st.success("🎉 **Experiment Complete!** You have successfully finished all discussion topics. Please return to the post-survey.")
    st.stop()

current_topic_key = TOPICS_ORDER[st.session_state.topic_index]

# --- 2. Sidebar Setup (Moved Info Box Here) ---
with st.sidebar:
    st.header("Session Setup")
    
    # Participant ID input
    p_id_input = st.number_input("Participant ID", min_value=1, step=1, value=st.session_state.participant_id, placeholder="e.g., 1")
    st.session_state.participant_id = p_id_input
    
    if st.session_state.participant_id is None:
        st.warning("⚠️ Please enter your Participant ID to begin.")
        st.stop()
        
    st.divider()
    
    # Moved the Instructions, Rules & Questions to Sidebar
    st.info(f"""
    **Discussion Topics for {TOPIC_NAMES[current_topic_key]}:**
    
    *Please read the statements below. Start the discussion by typing your opinion on the first statement.*
    
    📌 **Rules:** You can send a maximum of **4 messages per statement**. If you finish early, click the **'Next Statement'** button below the chat.
    
    💡 **Hint to start:** You can simply state whether you agree or disagree and give a short reason.
    """)
    
    for question in TOPIC_QUESTIONS[current_topic_key]:
        st.markdown(question)

# --- Progress Tracker Math ---
MAX_TURNS_PER_TOPIC = 12
if st.session_state.user_message_count < 4:
    current_stmt = "Statement 1"
    used_in_stmt = st.session_state.user_message_count
elif st.session_state.user_message_count < 8:
    current_stmt = "Statement 2"
    used_in_stmt = st.session_state.user_message_count - 4
else:
    current_stmt = "Statement 3"
    used_in_stmt = st.session_state.user_message_count - 8

# --- 3. Chat Interface ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. Transition Logic & Next/Finish Buttons ---
chat_disabled = False

# Auto-Transition Logic when 12 messages are reached
if st.session_state.user_message_count >= MAX_TURNS_PER_TOPIC:
    chat_disabled = True
    st.warning(f"✅ You have completed the discussion for **{TOPIC_NAMES[current_topic_key]}**.")
    
    # Button to move to the next main topic
    if st.button("➡️ Proceed to Next Topic"):
        st.session_state.topic_index += 1
        st.session_state.user_message_count = 0
        st.session_state.messages = []
        st.rerun()

# Skip/Next Statement Button
elif st.session_state.user_message_count % 4 != 0:
    col1, col2 = st.columns([0.8, 0.2])
    with col2:
        if st.session_state.user_message_count < 8:
            if st.button("⏭️ Next Statement"):
                if st.session_state.user_message_count < 4:
                    st.session_state.user_message_count = 4
                    sys_msg = "🔔 **System Notice:** You moved to **Statement 2**. Please share your opinion."
                else:
                    st.session_state.user_message_count = 8
                    sys_msg = "🔔 **System Notice:** You moved to **Statement 3**. Please share your opinion."
                st.session_state.messages.append({"role": "assistant", "content": sys_msg})
                st.rerun()
        else:
            if st.button("✅ Finish Topic"):
                st.session_state.user_message_count = 12
                st.rerun()

# --- 5. Status Text & Chat Input ---
status_text = f"💬 Current Focus: **{current_stmt}** ({used_in_stmt}/4 messages used) | Total Session: {st.session_state.user_message_count}/{MAX_TURNS_PER_TOPIC}"

if not chat_disabled:
    # Text right above the chat input
    st.caption(status_text)

# Dynamic Placeholder inside the input box
input_placeholder = f"Type your message here... [{current_stmt}: {used_in_stmt}/4 used]"

if prompt := st.chat_input(input_placeholder, disabled=chat_disabled):
    st.session_state.user_message_count += 1
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    history_for_api = st.session_state.messages.copy()
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    try:
        payload = {
            "message": prompt, 
            "history": history_for_api,
            "participant_id": st.session_state.participant_id,
            "participant_topic": current_topic_key
        }
        
        response = requests.post(FLASK_URL, json=payload)
        
        if response.status_code == 200:
            reply = response.json().get("reply")
            st.session_state.messages.append({"role": "assistant", "content": reply})
            
            # --- Auto-inject transition notices ---
            if st.session_state.user_message_count == 4:
                sys_msg = "🔔 **System Notice:** You have reached the limit of 4 messages for the first statement. Please start discussing **Statement 2** now."
                st.session_state.messages.append({"role": "assistant", "content": sys_msg})
                    
            elif st.session_state.user_message_count == 8:
                sys_msg = "🔔 **System Notice:** You have reached the limit of 4 messages for the second statement. Please start discussing **Statement 3** now."
                st.session_state.messages.append({"role": "assistant", "content": sys_msg})
            
            st.rerun()
                
        else:
            st.error(f"Backend Error: {response.json().get('error')}")
            
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the Flask backend. Make sure app.py is running!")