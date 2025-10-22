# app.py
import streamlit as st
from pathlib import Path
from scripts.teaching_assistant import StaticsMechanicsTA

# ---------- PAGE SETUP ----------
st.set_page_config(
    page_title="ARIA: Teaching Assistant for Renal Physiology",
    page_icon="🩸",
    layout="wide",
)

# ---------- STYLING ----------
st.markdown(
    """
    <style>
    body {
        background-color: #f7f7f5;
        color: #1e1e1e;
        font-family: 'Inter', sans-serif;
    }
    .main {
        padding: 2rem 3rem;
    }
    .stChatMessage {
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .user-msg {
        background-color: #e0f7fa;
    }
    .ai-msg {
        background-color: #f2f2f2;
        border-left: 4px solid #0c7bdc;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- HEADER ----------
st.title("🩺 PHRD 327: Renal System")
st.markdown(
    """
    <p style='font-size:17px; color:#444;'>
    ARIA is your interactive assistant for <b>Renal Physiology & Pathophysiology</b>.
    It answers questions, explains mechanisms, and cites your local course materials.
    </p>
    """,
    unsafe_allow_html=True,
)

# ---------- SESSION STATE ----------
if "ta" not in st.session_state:
    st.session_state.ta = StaticsMechanicsTA(base_path=".", api_key=st.secrets["OPENAI_API_KEY"])
if "history" not in st.session_state:
    st.session_state.history = []

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("Configuration ⚙️")
    st.success("TA System Ready")
    st.markdown("**Session ID:** " + st.session_state.ta.get_session_id())
    if st.button("🔄 Start New Session"):
        st.session_state.ta.new_session()
        st.session_state.history = []
        st.rerun()

    st.divider()
    st.markdown("### Tips for Better Questions")
    st.markdown(
        """
        - Ask stepwise about filtration, reabsorption, or clearance.  
        - Include hormones or segments (e.g., *loop of Henle, RAAS*).  
        - Request key equations or interpretation help.  
        - ARIA uses your uploaded renal PDFs for context.
        """
    )

# ---------- MAIN CHAT ----------
prompt = st.chat_input("Ask a renal physiology question...")
if prompt:
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.spinner("Thinking..."):
        result = st.session_state.ta.generate_response(prompt, st.session_state.history)
    st.session_state.history.append({"role": "assistant", "content": result["response"]})

# ---------- DISPLAY CHAT ----------
for msg in st.session_state.history:
    role = msg["role"]
    if role == "user":
        st.markdown(f"<div class='stChatMessage user-msg'><b>You:</b> {msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='stChatMessage ai-msg'><b>ARIA:</b> {msg['content']}</div>", unsafe_allow_html=True)

# ---------- FOOTER ----------
st.divider()
st.markdown(
    "<p style='text-align:center; color:gray; font-size:13px;'>"
    "ARIA © 2025 — Renal Physiology Tutor | Built with Streamlit"
    "</p>",
    unsafe_allow_html=True,
)


