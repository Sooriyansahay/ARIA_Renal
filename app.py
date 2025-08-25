import streamlit as st
import sys
from pathlib import Path
import os
import json
from datetime import datetime
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

from scripts.teaching_assistant import StaticsMechanicsTA
from scripts.database.feedback_storage import feedback_storage
from scripts.database.conversation_storage import conversation_storage
from scripts.database.supabase_config import supabase_config

# Get API key from environment variables or Streamlit secrets
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except Exception:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        st.error("OpenAI API key not found. Please set it in Streamlit secrets or environment variables.")
        st.stop()

# Page configuration
st.set_page_config(
    page_title="ARIA: Statics and Mechanics of Materials (EN.560.201) TA",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Header toggle styling
st.markdown("""
<style>
button[data-testid="collapsedControl"]{
  position: relative;
  width: 36px !important;
  height: 36px !important;
  padding: 4px !important;
  border: 1px solid #26272b;
  border-radius: 10px;
  background: #0e0f12;
  cursor: pointer;
}
button[data-testid="collapsedControl"] *{ opacity: 0 !important; font-size: 0 !important; line-height: 0 !important; }
button[data-testid="collapsedControl"]::after{
  content: ""; position: absolute; inset: 0; margin: auto; width: 22px; height: 22px;
  background-color: #d4d4d6;
  -webkit-mask: url("data:image/svg+xml;utf8,\
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'>\
  <path d='M8.59 16.59 13.17 12 8.59 7.41 10 6l6 6-6 6z'/>\
  <path d='M4.59 16.59 9.17 12 4.59 7.41 6 6l6 6-6 6z'/>\
</svg>") no-repeat center / contain;
          mask: url("data:image/svg+xml;utf8,\
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'>\
  <path d='M8.59 16.59 13.17 12 8.59 7.41 10 6l6 6-6 6z'/>\
  <path d='M4.59 16.59 9.17 12 4.59 7.41 6 6l6 6-6 6z'/>\
</svg>") no-repeat center / contain;
}
button[data-testid="collapsedControl"]:hover::after{ background-color: #ffffff; }
button[data-testid="collapsedControl"]:focus{ outline: 2px solid #6aa6ff; outline-offset: 2px; }
</style>
""", unsafe_allow_html=True)

# Theme and component tokens
st.markdown("""
<style>
:root{
  /* Paper-like yellow brown palette */
  --bg:#F5F1E8; --panel:#FEFCF7; --panel-2:#F9F5EC;
  --text:#2D2417; --muted:#8B7355; --border:#D4A574;
  --accent:#B8956A; --accent-2:#A0845C; --accent-hover:#8B7355;
  --callout-bg:#F0E6D2;

  /* Links */
  --link:#6E5637; --link-hover:#8B7355;

  /* Inputs and primary button */
  --input-bg:#FBF8F1; --input-border:#E6D4B7; --input-text:var(--text);
  --input-focus-border:var(--accent-2); --input-focus-ring:rgba(180,149,106,0.15);

  --primary-btn-bg:#E6D4B7; --primary-btn-border:#D4A574; --primary-btn-text:var(--text);
  --primary-btn-bg-hover:var(--accent); --primary-btn-border-hover:var(--accent);
  --primary-btn-text-hover:#ffffff;

  /* Conversation bubbles */
  --chat-student-bg:#0F1419; --chat-student-text:#F2EDE5; --chat-student-border:#C7A06B;
  --chat-assistant-bg:#1A1411; --chat-assistant-text:#F2EDE5; --chat-assistant-border:#A47A4F;

  /* Feedback buttons */
  --fb-bg:#FBF8F1; --fb-border:#E6D4B7; --fb-text:#5E4B33;
  --fb-selected:#D4A574; --fb-selected-text:#1a120a;
}

/* Global typography */
html, body, .stApp, .main, .block-container,
h1,h2,h3,h4,h5,h6,
p,div,span,label,li,small,em,strong,
button, input, textarea, select,
code, pre, kbd, samp {
  font-family: "Cambria", "Times New Roman", serif !important;
  -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;
  color: var(--text);
}

a { color: var(--link) !important; text-decoration: none; }
a:hover { color: var(--link-hover) !important; text-decoration: underline; }

.stApp{ background-color:var(--bg); }
.main .block-container{ max-width:960px; padding:2rem 1.5rem; background:var(--bg); }

/* Title */
.app-title{ text-align:center; font-weight:700; line-height:1.2; margin:0 0 1rem 0; letter-spacing:.2px;
  font-size:clamp(2.6rem, 2.8vw + 2rem, 3.6rem); }

/* Sidebar */
[data-testid="stSidebar"]{
  background:var(--panel);
  border-right:1px solid var(--border);
  box-shadow:2px 0 8px rgba(0,0,0,.15);
  padding-top:.5rem;
}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3{
  border-bottom:1px solid var(--border); padding-bottom:.5rem; margin-bottom:.75rem;
}

/* Base inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > select{
  background:var(--panel-2); color:var(--text) !important; border:1px solid var(--border) !important;
  border-radius:12px; padding:.75rem .9rem; transition:border .15s ease, box-shadow .15s ease;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stSelectbox > div > div > select:focus{
  border-color:var(--accent) !important; box-shadow:0 0 0 3px rgba(106,166,255,.18) !important; outline:none;
}

/* Focus Area selectbox theme aware */
.stSelectbox > div > div > select{
  background: var(--input-bg) !important; color: var(--input-text) !important;
  border: 1px solid var(--input-border) !important; border-radius: 12px !important;
}
.stSelectbox > div > div > select:focus{
  border-color: var(--input-focus-border) !important;
  box-shadow: 0 0 0 3px var(--input-focus-ring) !important;
}

/* Generic buttons */
.stButton > button{
  background:var(--panel-2); color:var(--text); border:1px solid var(--border);
  border-radius:12px; padding:.7rem 1.1rem; font-weight:700;
  transition:transform .08s ease, background .15s ease, border .15s ease, color .15s ease;
}
.stButton > button:hover{ background:var(--accent-hover); border-color:var(--accent); transform:translateY(-1px); color:white; }

/* Ask ARIA button theme aware */
.stForm .stButton > button{
  background: var(--primary-btn-bg) !important; color: var(--primary-btn-text) !important;
  border: 1px solid var(--primary-btn-border) !important; font-weight: 700 !important;
  border-radius: 12px !important;
}
.stForm .stButton > button:hover{
  background: var(--primary-btn-bg-hover) !important; color: var(--primary-btn-text-hover) !important;
  border-color: var(--primary-btn-border-hover) !important; transform: translateY(-1px) !important;
}

/* Callout */
.aria-callout{
  position:relative; background:var(--callout-bg);
  border-radius:14px; padding:1.5rem 1.25rem; box-shadow:0 4px 12px rgba(180, 149, 106, 0.15), inset 0 0 0 1px rgba(180, 149, 106, 0.2);
  text-align: center; border: 1px solid var(--border);
}
.aria-callout::before{ content:""; position:absolute; left:0; top:0; bottom:0; width:6px; background:var(--accent);
  border-top-left-radius:14px; border-bottom-left-radius:14px; }
.aria-callout .welcome-main { font-size: 1.1rem; line-height: 1.4; margin-bottom: 0.75rem; color: var(--text); }
.aria-callout .welcome-sub { font-size: 1rem; color: var(--muted); font-style: italic; }

/* Conversation messages */
.chat-message{
  padding:1.05rem 1.15rem; border-radius:14px; margin:1rem 0; border:1px solid var(--border);
  box-shadow:0 1px 6px rgba(0,0,0,.12);
}
.student-message{
  background: var(--chat-student-bg);
  color: var(--chat-student-text);
  border-left: 4px solid var(--chat-student-border);
}
.ta-message{
  background: var(--chat-assistant-bg);
  color: var(--chat-assistant-text);
  border-left: 4px solid var(--chat-assistant-border);
}
.student-message *, .ta-message *{ color: inherit; }   /* ensure inner text inherits bubble color */

/* Feedback bar and buttons */
.feedback-container{ display:flex; align-items:center; gap:.5rem; margin-top:.75rem; padding-top:.75rem; border-top:1px solid var(--border); opacity:.95; }
.feedback-text{ font-size:.9rem; color:var(--muted); margin-right:.5rem; }
.feedback-button{
  background:var(--fb-bg); border:1px solid var(--fb-border); border-radius:10px;
  padding:.55rem 1rem; cursor:pointer; transition:all .15s ease;
  color:var(--fb-text); font-size:.92rem; min-width:9rem;
}
.feedback-button:hover{ filter: brightness(0.98); border-color:var(--accent); }
.feedback-button.selected{ background:var(--fb-selected); color:var(--fb-selected-text); border-color:var(--fb-selected); transform:translateY(-1px); }

/* Code blocks */
pre{ background:#0f1012 !important; border:1px solid var(--border) !important; border-radius:10px !important; padding:1rem !important; overflow-x:auto !important; }

/* Header bar */
[data-testid="stHeader"] { background-color: rgba(0, 0, 0, 0.9) !important; }
[data-testid="stHeader"] button, [data-testid="stHeader"] svg { color: #F5F1E8 !important; fill: #F5F1E8 !important; }

/* Dark preference overrides */
@media (prefers-color-scheme: dark){
  :root{
    --bg:#2A1F15; --panel:#3B2D1E; --panel-2:#342619;
    --text:#F5F1E8; --muted:#D0B894; --border:#5D4A37;
    --accent:#D4A574; --accent-2:#E6B885; --accent-hover:#F0C896; --callout-bg:#3C2E1E;

    --link:#E6B885; --link-hover:#F0C896;

    --input-bg: var(--panel-2); --input-border: var(--border); --input-text: var(--text);
    --input-focus-border: var(--accent-2); --input-focus-ring: rgba(212,165,116,0.25);

    --primary-btn-bg: var(--accent); --primary-btn-border: var(--accent); --primary-btn-text: #1b130a;
    --primary-btn-bg-hover: var(--accent-hover); --primary-btn-border-hover: var(--accent-hover); --primary-btn-text-hover: #0b0906;

    --chat-student-bg:#0E1116; --chat-student-text:#F2EDE5; --chat-student-border:#D7B07A;
    --chat-assistant-bg:#15100D; --chat-assistant-text:#F2EDE5; --chat-assistant-border:#C79A66;

    --fb-bg:#2E2318; --fb-border:#5D4A37; --fb-text:#E8DCC6; --fb-selected:#D4A574; --fb-selected-text:#1b130a;
  }
  .stApp{ background:var(--bg); color:var(--text); }
  .main .block-container{ background:var(--bg); }
  .stButton > button{ background:var(--panel-2); }
  .aria-callout{ background:var(--callout-bg); }
}

/* Comfortable base font size, keep title size */
:root { --app-font-size: 1.15rem; }
body, .stApp, .main .block-container,
p, div, span, label, li, small, em, strong,
.stMarkdown, .stTextInput *, .stTextArea *, .stSelectbox *,
.stButton > button, code, pre, kbd, samp {
  font-size: var(--app-font-size) !important;
  line-height: 1.35 !important;
}
h1.app-title{ font-size: clamp(2.6rem, 2.8vw + 2rem, 3.6rem) !important; }

/* Feedback buttons sizing to avoid wrapping */
.stButton > button{ white-space: nowrap !important; min-width: 10.5rem !important; font-size: 0.95rem !important; padding: 0.55rem 1rem !important; }

/* Footer */
.app-footer{ text-align:center; color:var(--muted); font-size:1rem; margin-top:1rem; }
</style>
""", unsafe_allow_html=True)

# Session state
if "ta_system" not in st.session_state:
    st.session_state.ta_system = None
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "system_initialized" not in st.session_state:
    st.session_state.system_initialized = False
if "feedback_data" not in st.session_state:
    st.session_state.feedback_data = []
if "message_feedback" not in st.session_state:
    st.session_state.message_feedback = {}
if "last_question_count" not in st.session_state:
    st.session_state.last_question_count = 0

def initialize_ta_system():
    try:
        base_path = str(Path(__file__).parent)
        ta_system = StaticsMechanicsTA(base_path, OPENAI_API_KEY)
        return ta_system
    except Exception as e:
        st.error(f"Failed to initialize TA system: {e}")
        return None

@st.cache_data(ttl=3600)
def get_course_topics():
    return [
        "Rigid Body Equilibrium", "Force Systems", "Moments", "Trusses",
        "Frames and Machines", "Stress and Strain", "Axial Force Members",
        "Torsion", "Bending", "Shear", "Deflections", "Centroids",
        "Moment of Inertia", "Stress Transformation", "Principal Stresses"
    ]

def update_conversation_feedback(conversation_id, feedback_type):
    try:
        success = feedback_storage.update_feedback(
            conversation_id=conversation_id,
            feedback_type=feedback_type
        )
        if not success:
            st.error("Failed to update feedback")
        return success
    except Exception as e:
        st.error(f"Error updating feedback: {e}")
        return False

def get_conversation_feedback(conversation_id):
    try:
        return feedback_storage.get_conversation_feedback(conversation_id)
    except Exception as e:
        st.error(f"Error getting feedback: {e}")
        return None

def clear_conversation_feedback(conversation_id):
    try:
        success = feedback_storage.clear_conversation_feedback(conversation_id)
        return success
    except Exception as e:
        st.error(f"Error clearing feedback: {e}")
        return False

def handle_feedback(message_index, feedback_type):
    if message_index < len(st.session_state.conversation_history):
        message = st.session_state.conversation_history[message_index]
        if message["role"] == "assistant":
            conversation_id = message.get("conversation_id")
            if not conversation_id:
                st.error("No conversation ID found for this message")
                return
            current_feedback = st.session_state.message_feedback.get(message_index)
            if current_feedback == feedback_type:
                success = clear_conversation_feedback(conversation_id)
                if success:
                    if message_index in st.session_state.message_feedback:
                        del st.session_state.message_feedback[message_index]
                    st.session_state.feedback_data = [entry for entry in st.session_state.feedback_data if entry.get("message_index") != message_index]
            else:
                success = update_conversation_feedback(conversation_id, feedback_type)
                if success:
                    st.session_state.message_feedback[message_index] = feedback_type
                    user_question = st.session_state.conversation_history[message_index-1]["content"] if message_index > 0 else ""
                    ai_response = message["content"]
                    concepts_covered = message.get("concepts", [])
                    response_time = message.get("response_time", 0)
                    feedback_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "message_index": message_index,
                        "conversation_id": conversation_id,
                        "user_question": user_question,
                        "ta_response": ai_response,
                        "feedback": feedback_type,
                        "concepts_covered": concepts_covered,
                        "response_time": response_time
                    }
                    st.session_state.feedback_data = [entry for entry in st.session_state.feedback_data if entry.get("message_index") != message_index]
                    st.session_state.feedback_data.append(feedback_entry)
            st.rerun()

def main():
    if not st.session_state.system_initialized:
        with st.spinner("Initializing TA system"):
            ta_system = initialize_ta_system()
            if ta_system:
                st.session_state.ta_system = ta_system
                st.session_state.system_initialized = True
            else:
                st.error("Failed to initialize TA system. Check the API key.")
                return

    st.markdown('<h1 class="app-title">ARIA: Statics and Mechanics of Materials (EN.560.201) TA</h1>', unsafe_allow_html=True)

    if st.session_state.system_initialized:
        st.markdown("""
            <div class="aria-callout">
              <div class="welcome-main">I am ARIA, your teaching assistant for Statics and Mechanics of Materials. I will guide you through problem solving steps and help you understand key concepts.</div>
              <div class="welcome-sub">How can I help you today?</div>
            </div>
            """, unsafe_allow_html=True)

    with st.sidebar:
        st.header("Configuration")
        if st.session_state.system_initialized:
            st.success("TA System Ready")
        else:
            st.error("System Not Ready")

        st.subheader("Focus Area")
        topics = get_course_topics()
        selected_topic = st.selectbox("Select a topic to focus on (optional)", ["All Topics"] + topics)

        st.subheader("Conversation")
        if st.button("Clear Conversation"):
            st.session_state.conversation_history = []
            st.rerun()

        st.subheader("Tips for Better Learning")
        st.markdown("""
        * Ask specific questions about concepts
        * Describe your problem step by step
        * Ask for guidance, not direct answers
        * Request examples or analogies
        * Ask about common mistakes to avoid
        """)

    if st.session_state.system_initialized and st.session_state.ta_system:
        for i, msg in enumerate(st.session_state.conversation_history):
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-message student-message"><strong>You</strong><br>{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message ta-message"><strong>ARIA</strong><br>{msg["content"]}</div>', unsafe_allow_html=True)

                current_feedback = st.session_state.message_feedback.get(i, None)
                user_messages_count = len([m for m in st.session_state.conversation_history if m["role"] == "user"])
                message_question_index = len([m for m in st.session_state.conversation_history[:i+1] if m["role"] == "user"])
                is_changeable = (message_question_index == user_messages_count)

                st.markdown("<div class='feedback-container'><span class='feedback-text'>Was this response helpful</span></div>", unsafe_allow_html=True)
                col1, col2, col3, _spacer = st.columns([2.8, 2.8, 2.8, 3.6])

                with col1:
                    button_type = "primary" if current_feedback == "helpful" else "secondary"
                    if st.button("Helpful", key=f"helpful_{i}", help="This response was helpful" if is_changeable else "Feedback locked after new question", type=button_type, disabled=not is_changeable, use_container_width=True):
                        handle_feedback(i, "helpful")

                with col2:
                    button_type = "primary" if current_feedback == "not_helpful" else "secondary"
                    if st.button("Not Helpful", key=f"not_helpful_{i}", help="This response was not helpful" if is_changeable else "Feedback locked after new question", type=button_type, disabled=not is_changeable, use_container_width=True):
                        handle_feedback(i, "not_helpful")

                with col3:
                    button_type = "primary" if current_feedback == "partially_helpful" else "secondary"
                    if st.button("Partially", key=f"partial_{i}", help="This response was partially helpful" if is_changeable else "Feedback locked after new question", type=button_type, disabled=not is_changeable, use_container_width=True):
                        handle_feedback(i, "partially_helpful")

                if current_feedback:
                    if is_changeable:
                        feedback_text = {
                            "helpful": "You marked this helpful. Click to change",
                            "not_helpful": "You marked this not helpful. Click to change",
                            "partially_helpful": "You marked this partially helpful. Click to change"
                        }
                    else:
                        feedback_text = {
                            "helpful": "Marked as helpful",
                            "not_helpful": "Marked as not helpful",
                            "partially_helpful": "Marked as partially helpful"
                        }
                    st.markdown(f"<small style='color: var(--muted);'>{feedback_text[current_feedback]}</small>", unsafe_allow_html=True)

                st.divider()

        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_area("Ask your question", placeholder="For example, how to calculate the moment about point A in a beam problem", height=100)
            col1, col2 = st.columns([1, 4])
            with col1:
                submit_button = st.form_submit_button("Ask ARIA", use_container_width=True)

            if submit_button and user_input:
                current_question_count = len([m for m in st.session_state.conversation_history if m["role"] == "user"])
                st.session_state.last_question_count = current_question_count + 1

                st.session_state.conversation_history.append({ "role": "user", "content": user_input })
                with st.spinner("ARIA is thinking"):
                    try:
                        if "session_id" not in st.session_state:
                            st.session_state.session_id = conversation_storage.create_session_id()

                        start_time = time.time()
                        response_data = st.session_state.ta_system.generate_response(
                            user_input,
                            st.session_state.conversation_history[-10:]
                        )
                        response_time = time.time() - start_time

                        conversation_id = None
                        if supabase_config.is_connected():
                            conversation_id = conversation_storage.store_conversation(
                                session_id=st.session_state.session_id,
                                user_question=user_input,
                                ta_response=response_data["response"],
                                context_sources=response_data.get("context_sources", []),
                                concepts_used=response_data.get("concepts_covered", []),
                                response_time=response_time
                            )

                        ta_message = {
                            "role": "assistant",
                            "content": response_data["response"],
                            "concepts": response_data.get("concepts_covered", []),
                            "response_time": response_time,
                            "conversation_id": conversation_id
                        }
                        st.session_state.conversation_history.append(ta_message)
                        with st.sidebar:
                            st.metric("Response Time", f"{response_time:.2f}s")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error generating response: {e}")
    else:
        st.markdown("""
        ## Welcome to your Statics and Mechanics Teaching Assistant

        This assistant helps you learn by
        Guiding you through problem solving steps
        Explaining key concepts and formulas
        Providing hints and examples
        Asking questions to check your understanding

        Important
        This assistant will not give direct answers. It will help you develop problem solving skills.

        The system initializes automatically.
        """)

        st.subheader("Example Questions You Can Ask")
        examples = [
            "How do I start analyzing a truss structure",
            "What is the difference between stress and strain",
            "Can you guide me through setting up equilibrium equations",
            "What are the key steps for calculating beam deflections",
            "How do I determine if a structure is statically determinate"
        ]
        for example in examples:
            st.markdown(f"• {example}")

    st.divider()
    st.markdown(
        '<div class="app-footer"><div>Built by Dibakar Roy Sarkar and Yue Luo, Centrum Intelliphysics Lab (Somdatta Goswami),</div><div>Civil and System Engineering, Johns Hopkins University</div></div>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
