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
    page_title="ARIA: Teaching Assistant for Statics and Mechanics of Materials (EN.560.201)",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* Make the toggle a clean icon button and hide any inner text */
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

/* Hide whatever Streamlit puts inside (e.g., 'keyboard_double_arrow_right') */
button[data-testid="collapsedControl"] *{
  opacity: 0 !important;
  font-size: 0 !important;
  line-height: 0 !important;
}

/* Draw a crisp double-chevron icon with an inline SVG mask */
button[data-testid="collapsedControl"]::after{
  content: "";
  position: absolute;
  inset: 0;
  margin: auto;
  width: 22px;
  height: 22px;

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

/* Hover and focus states */
button[data-testid="collapsedControl"]:hover::after{ background-color: #ffffff; }
button[data-testid="collapsedControl"]:focus{ outline: 2px solid #6aa6ff; outline-offset: 2px; }
</style>
""", unsafe_allow_html=True)

# Design CSS with Cambria font and yellowish-brown color scheme
st.markdown("""
<style>
:root{
  --bg:#F5F1E8; --panel:#FEFCF7; --panel-2:#F9F5EC;
  --text:#3C2E1E; --muted:#8B7355; --border:#D4A574;
  --accent:#B8956A; --accent-2:#A0845C;
  --accent-hover:#8B7355; --callout-bg:#F0E6D2;
  --claude-purple:#a47aff;
}

/* Apply Cambria globally, including code blocks */
html, body, .stApp, .main, .block-container,
h1,h2,h3,h4,h5,h6,
p,div,span,label,li,small,em,strong,
button, input, textarea, select,
code, pre, kbd, samp {
  font-family: "Cambria", "Times New Roman", serif !important;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--text);
}

.stApp{ background-color:var(--bg); }

.main .block-container{ max-width:960px; padding:2rem 1.5rem; background:var(--bg); }

/* Centered larger app title */
.app-title{
  text-align:center;
  font-weight:700;
  line-height:1.2;
  margin:0 0 1rem 0;
  letter-spacing:.2px;
  font-size:clamp(2.6rem, 2.8vw + 2rem, 3.6rem);
}

/* Headings scale */
h2{font-size:1.8rem !important}
h3{font-size:1.4rem !important}

/* Sidebar */
[data-testid="stSidebar"]{
  background:var(--panel); border-right:1px solid var(--border); box-shadow:2px 0 8px rgba(0,0,0,.25); padding-top:.5rem;
}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3{
  border-bottom:1px solid var(--border); padding-bottom:.5rem; margin-bottom:.75rem;
}

/* Inputs */
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

/* General Buttons - Enhanced visibility */
.stButton > button{
  background:var(--panel-2) !important; 
  color:var(--text) !important; 
  border:2px solid var(--border) !important;
  border-radius:8px !important; 
  padding:.7rem 1.1rem !important; 
  font-weight:700 !important;
  font-size:0.95rem !important;
  transition:all .2s ease !important;
  box-shadow:0 1px 3px rgba(0,0,0,0.1) !important;
}
.stButton > button:hover{ 
  background:var(--accent-hover) !important; 
  border-color:var(--accent) !important; 
  transform:translateY(-1px) !important; 
  color:white !important;
  box-shadow:0 2px 6px rgba(0,0,0,0.15) !important;
}

/* Clear Conversation button specific styling */
[data-testid="stSidebar"] .stButton > button {
  background:var(--accent-2) !important;
  color:var(--text) !important;
  border:2px solid var(--accent) !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background:var(--accent) !important;
  color:white !important;
}

/* Focus Area Selectbox - Enhanced visibility for both themes */
.stSelectbox > div > div > select{
  background:var(--panel-2) !important; 
  color:var(--text) !important; 
  border:2px solid var(--border) !important;
  border-radius:8px !important;
  font-weight:600 !important;
  font-size:1rem !important;
  padding:0.5rem 0.75rem !important;
  -webkit-appearance:none !important;
  -moz-appearance:none !important;
  appearance:none !important;
}
.stSelectbox > div > div > select:focus{
  border-color:var(--accent) !important; 
  box-shadow:0 0 0 3px rgba(180, 149, 106, 0.25) !important;
  outline:none !important;
}

/* Custom dropdown arrow */
.stSelectbox > div > div {
  position:relative !important;
}
.stSelectbox > div > div::after {
  content:'▼' !important;
  position:absolute !important;
  right:12px !important;
  top:50% !important;
  transform:translateY(-50%) !important;
  pointer-events:none !important;
  color:var(--text) !important;
  font-size:0.8rem !important;
}

/* Dropdown menu options styling */
.stSelectbox > div > div > select option {
  background:var(--panel) !important;
  color:var(--text) !important;
  padding:8px 12px !important;
  font-weight:500 !important;
  border:none !important;
}
.stSelectbox > div > div > select option:hover,
.stSelectbox > div > div > select option:focus,
.stSelectbox > div > div > select option:checked {
  background:var(--accent) !important;
  color:white !important;
}

/* Streamlit selectbox widget specific styling - Enhanced visibility */
[data-baseweb="select"] {
  background:var(--panel-2) !important;
}
[data-baseweb="select"] > div {
  background:var(--panel-2) !important;
  color:var(--text) !important;
  border:2px solid var(--border) !important;
  border-radius:8px !important;
}

/* Dropdown popover container - High contrast background */
[data-baseweb="popover"] {
  background:var(--bg) !important;
  border:3px solid var(--accent) !important;
  border-radius:10px !important;
  box-shadow:0 6px 20px rgba(0,0,0,0.3) !important;
  z-index:9999 !important;
}

/* Dropdown menu container */
[data-baseweb="menu"] {
  background:var(--bg) !important;
  border-radius:8px !important;
  padding:4px !important;
}

/* Individual menu items - High contrast */
[data-baseweb="menu"] li {
  background:var(--panel-2) !important;
  color:var(--text) !important;
  padding:12px 16px !important;
  margin:2px 0 !important;
  border-radius:6px !important;
  font-weight:600 !important;
  font-size:1rem !important;
  border:1px solid var(--border) !important;
  transition:all 0.2s ease !important;
}

/* Menu item hover state */
[data-baseweb="menu"] li:hover {
  background:var(--accent) !important;
  color:white !important;
  border-color:var(--accent) !important;
  transform:translateX(4px) !important;
  box-shadow:0 2px 6px rgba(0,0,0,0.15) !important;
}

/* Menu item selected state */
[data-baseweb="menu"] li[aria-selected="true"] {
  background:var(--accent-2) !important;
  color:var(--text) !important;
  border-color:var(--accent) !important;
  font-weight:700 !important;
}

/* Additional fallback styling for dropdown visibility */
.stSelectbox [role="listbox"] {
  background:var(--bg) !important;
  border:2px solid var(--accent) !important;
  border-radius:8px !important;
}

.stSelectbox [role="option"] {
  background:var(--panel-2) !important;
  color:var(--text) !important;
  padding:8px 16px !important;
  border-radius:4px !important;
  margin:2px !important;
  font-weight:600 !important;
}

.stSelectbox [role="option"]:hover,
.stSelectbox [role="option"][aria-selected="true"] {
  background:var(--accent) !important;
  color:white !important;
}

/* Force text visibility in all dropdown states */
.stSelectbox * {
  color:var(--text) !important;
}
.stSelectbox [role="option"] * {
  color:inherit !important;
}

/* Ask ARIA button - Enhanced visibility and contrast */
.stForm .stButton > button{
  background:var(--accent) !important; 
  color:white !important; 
  border:3px solid var(--accent) !important; 
  font-weight:800 !important;
  font-size:1.1rem !important;
  border-radius:10px !important;
  padding:0.8rem 1.5rem !important;
  box-shadow:0 3px 6px rgba(0,0,0,0.15) !important;
  transition:all 0.2s ease !important;
  text-transform:uppercase !important;
  letter-spacing:0.5px !important;
  min-height:48px !important;
}
.stForm .stButton > button:hover{
  background:var(--accent-hover) !important; 
  color:white !important; 
  border-color:var(--accent-hover) !important;
  transform:translateY(-3px) !important;
  box-shadow:0 6px 12px rgba(0,0,0,0.25) !important;
}
.stForm .stButton > button:active{
  transform:translateY(-1px) !important;
  box-shadow:0 2px 4px rgba(0,0,0,0.15) !important;
}

/* Darken placeholder text for better contrast */
.stTextArea > div > div > textarea::placeholder{
  color:var(--text) !important; opacity:0.7 !important;
}
.stTextArea > div > div > textarea{
  color:var(--text) !important;
}

/* Single rail callout with yellowish-brown styling */
.aria-callout{
  position:relative; background:var(--callout-bg);
  border-radius:14px; padding:1.5rem 1.25rem; box-shadow:0 4px 12px rgba(180, 149, 106, 0.15), inset 0 0 0 1px rgba(180, 149, 106, 0.2);
  text-align: center; border: 1px solid var(--border);
}
.aria-callout::before{
  content:""; position:absolute; left:0; top:0; bottom:0; width:6px;
  background:var(--accent); border-top-left-radius:14px; border-bottom-left-radius:14px;
}
.aria-callout .welcome-main {
  font-size: 1.1rem; line-height: 1.4; margin-bottom: 0.75rem; color: var(--text);
}
.aria-callout .welcome-sub {
  font-size: 1rem; color: var(--muted); font-style: italic;
}

/* Messages */
.chat-message{
  padding:1.1rem 1.2rem; border-radius:12px; margin:1rem 0; border:1px solid var(--border);
  background:var(--panel); box-shadow:0 1px 6px rgba(0,0,0,.18); color:var(--text);
}
.student-message{ 
  background:var(--panel-2); border-left:4px solid var(--accent); 
}
.ta-message{ 
  background:var(--panel); border-left:4px solid var(--claude-purple); 
}

/* Enhanced Feedback buttons */
.feedback-container{
  display:flex; align-items:center; gap:0.5rem; margin-top:0.75rem; padding-top:0.75rem;
  border-top:1px solid var(--border); opacity:0.9;
}
.feedback-text{
  font-size:0.9rem; color:var(--text); margin-right:0.5rem; font-weight:600;
}
.feedback-button{
  background:var(--panel-2) !important; 
  border:2px solid var(--border) !important; 
  border-radius:8px !important;
  padding:0.5rem 1rem !important; 
  cursor:pointer !important; 
  transition:all 0.2s ease !important;
  color:var(--text) !important; 
  font-size:0.85rem !important; 
  display:flex !important; 
  align-items:center !important; 
  gap:0.4rem !important;
  min-width:80px !important; 
  white-space:nowrap !important;
  font-weight:600 !important;
}
.feedback-button:hover{
  background:var(--accent-2) !important; 
  border-color:var(--accent) !important; 
  color:var(--text) !important;
  transform:translateY(-1px) !important;
}
.feedback-button.selected{
  background:var(--accent) !important; 
  border-color:var(--accent) !important; 
  color:white !important;
  transform:scale(1.05) !important;
}
.feedback-button.selected.negative{
  background:#dc3545 !important; 
  border-color:#dc3545 !important;
}
.feedback-button.selected.partial{
  background:#ffa500 !important; 
  border-color:#ffa500 !important;
}

/* Footer centered */
.app-footer{
  text-align:center;
  color:var(--muted);
  font-size:1rem;
  margin-top:1rem;
}

/* Code blocks keep CMU Serif but retain block styling */
pre{
  background:#0f1012 !important;
  border:1px solid var(--border) !important;
  border-radius:10px !important;
  padding:1rem !important;
  overflow-x:auto !important;
}

/* Navigation bar icons - White Share option for better visibility */
[data-testid="stHeader"] {
  background-color: rgba(0, 0, 0, 0.9) !important;
}
[data-testid="stHeader"] button {
  color: #F5F1E8 !important;
}
[data-testid="stHeader"] svg {
  fill: #F5F1E8 !important;
  color: #F5F1E8 !important;
}
[data-testid="stHeader"] [data-testid="stHeaderActionElements"] button {
  color: white !important;
}
[data-testid="stHeader"] [data-testid="stHeaderActionElements"] svg {
  fill: white !important;
}

/* Dark mode preference - maintain yellowish-brown theme */
@media (prefers-color-scheme: dark){
  :root{
    --bg:#2A1F15; --panel:#3C2E1E; --panel-2:#342619;
    --text:#F5F1E8; --muted:#B8956A; --border:#5D4A37;
    --accent:#D4A574; --accent-2:#E6B885;
    --accent-hover:#F0C896; --callout-bg:#3C2E1E;
    --claude-purple:#a47aff;
  }
  .stApp{ background:var(--bg); color:var(--text); }
  .main .block-container{ background:var(--bg); }
  .stButton > button{ background:var(--panel-2); color:var(--text); }
  .aria-callout{ background:var(--callout-bg); }
  .chat-message{ background:var(--panel); color:var(--text); }
  .student-message{ background:var(--panel-2); }
  .ta-message{ background:var(--panel); }
  
  /* Ensure all text elements are visible in dark mode */
  h1, h2, h3, h4, h5, h6, p, div, span, label, li, small, em, strong {
    color: var(--text) !important;
  }
  
  /* Sidebar styling in dark mode */
  [data-testid="stSidebar"] {
    background: var(--panel) !important;
    color: var(--text) !important;
  }
  [data-testid="stSidebar"] * {
    color: var(--text) !important;
  }
  
  /* Form elements in dark mode */
  .stTextInput > div > div > input,
  .stTextArea > div > div > textarea,
  .stSelectbox > div > div > select {
    background: var(--panel-2) !important;
    color: var(--text) !important;
    border: 2px solid var(--border) !important;
  }
  
  /* Enhanced button styling for dark mode */
  .stButton > button {
    background: var(--panel-2) !important;
    color: var(--text) !important;
    border: 2px solid var(--border) !important;
  }
  
  .stForm .stButton > button {
    background: var(--accent) !important;
    color: white !important;
    border: 3px solid var(--accent) !important;
  }
  
  /* Feedback buttons in dark mode */
  .feedback-button {
    background: var(--panel-2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
  }
  
  /* Selectbox dropdown and options in dark mode */
  .stSelectbox > div > div::after {
    color: var(--text) !important;
  }
  
  /* Streamlit selectbox widget dark mode overrides - Enhanced visibility */
  [data-baseweb="select"] {
    background: var(--panel-2) !important;
  }
  [data-baseweb="select"] > div {
    background: var(--panel-2) !important;
    color: var(--text) !important;
    border: 2px solid var(--border) !important;
  }
  
  /* Dark mode dropdown popover - High contrast */
  [data-baseweb="popover"] {
    background: var(--bg) !important;
    border: 3px solid var(--accent) !important;
    box-shadow: 0 8px 24px rgba(0,0,0,0.5) !important;
  }
  
  /* Dark mode dropdown menu */
  [data-baseweb="menu"] {
    background: var(--bg) !important;
  }
  
  /* Dark mode menu items - Maximum contrast */
  [data-baseweb="menu"] li {
    background: var(--panel-2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    font-weight: 600 !important;
  }
  
  /* Dark mode hover and selected states */
  [data-baseweb="menu"] li:hover {
    background: var(--accent) !important;
    color: white !important;
    border-color: var(--accent) !important;
  }
  
  [data-baseweb="menu"] li[aria-selected="true"] {
    background: var(--accent-2) !important;
    color: var(--text) !important;
    border-color: var(--accent) !important;
    font-weight: 700 !important;
  }
  
  /* Ensure proper contrast for labels */
  [data-testid="stSidebar"] label,
  .stSelectbox label,
  .stTextInput label,
  .stTextArea label {
    color: var(--text) !important;
    font-weight: 600 !important;
  }
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
:root { --app-font-size: 1.15rem; }

/* make everything bigger except the main title */
body, .stApp, .main .block-container,
p, div, span, label, li, small, em, strong,
.stMarkdown, .stTextInput *, .stTextArea *, .stSelectbox *,
.stButton > button, code, pre, kbd, samp {
  font-size: var(--app-font-size) !important;
  line-height: 1.35 !important;
}

/* keep your custom title size */
h1.app-title{
  font-size: clamp(2.6rem, 2.8vw + 2rem, 3.6rem) !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Feedback buttons: keep text on one line and give room */
.stButton > button{
  white-space: nowrap !important;       /* prevents Helpf / ul split */
  min-width: 10.5rem !important;        /* ~168px; adjust if you want wider */
  font-size: 0.95rem !important;        /* slightly smaller so it fits */
  padding: 0.55rem 1rem !important;
}
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
    """Update feedback for a conversation"""
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
    """Get feedback for a conversation"""
    try:
        return feedback_storage.get_conversation_feedback(conversation_id)
    except Exception as e:
        st.error(f"Error getting feedback: {e}")
        return None

def clear_conversation_feedback(conversation_id):
    """Clear feedback for a conversation"""
    try:
        success = feedback_storage.clear_conversation_feedback(conversation_id)
        return success
    except Exception as e:
        st.error(f"Error clearing feedback: {e}")
        return False

def handle_feedback(message_index, feedback_type):
    """Handle user feedback for a specific message"""
    if message_index < len(st.session_state.conversation_history):
        message = st.session_state.conversation_history[message_index]
        if message["role"] == "assistant":
            # Get conversation ID from the message
            conversation_id = message.get("conversation_id")
            if not conversation_id:
                st.error("No conversation ID found for this message")
                return
            
            current_feedback = st.session_state.message_feedback.get(message_index)
            
            # If clicking the same feedback type, remove it (toggle off)
            if current_feedback == feedback_type:
                # Clear feedback from database
                success = clear_conversation_feedback(conversation_id)
                if success:
                    # Remove from session state
                    if message_index in st.session_state.message_feedback:
                        del st.session_state.message_feedback[message_index]
                    
                    # Remove from feedback_data list (for backward compatibility)
                    st.session_state.feedback_data = [
                        entry for entry in st.session_state.feedback_data 
                        if entry.get("message_index") != message_index
                    ]
            else:
                # Update feedback in database
                success = update_conversation_feedback(conversation_id, feedback_type)
                
                if success:
                    # Update session state
                    st.session_state.message_feedback[message_index] = feedback_type
                    
                    # Update feedback_data list (for backward compatibility)
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
                    
                    # Remove any existing feedback for this message
                    st.session_state.feedback_data = [
                        entry for entry in st.session_state.feedback_data 
                        if entry.get("message_index") != message_index
                    ]
                    
                    # Add new feedback
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
    
    st.markdown(
    '<span class="app-title"><em>ARIA</em>: Teaching Assistant for Statics and Mechanics of Materials (EN.560.201)</span>',
        unsafe_allow_html=True
    )
    
    if st.session_state.system_initialized:
        st.markdown(
            """
            <div class="aria-callout">
              <div class="welcome-main">I am ARIA, your teaching assistant for Statics and Mechanics of Materials. I will guide you through problem solving steps and help you understand key concepts.</div>
              <div class="welcome-sub">How can I help you today?</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with st.sidebar:
        st.header("Configuration")
        if st.session_state.system_initialized:
            st.success("TA System Ready")
        else:
            st.error("System Not Ready")
        
        st.subheader("Focus Area")
        topics = get_course_topics()
        selected_topic = st.selectbox(
            "Select a topic to focus on (optional)",
            ["All Topics"] + topics
        )
        
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
                st.markdown(
                    f'<div class="chat-message student-message"><strong>You</strong><br>{msg["content"]}</div>',
                    unsafe_allow_html=True
                )
            else:
                # Display TA message
                st.markdown(
                    f'<div class="chat-message ta-message"><strong>ARIA</strong><br>{msg["content"]}</div>',
                    unsafe_allow_html=True
                )
                
                # Add feedback buttons
                current_feedback = st.session_state.message_feedback.get(i, None)
                
                # Check if this is the most recent TA response (feedback is changeable)
                user_messages_count = len([msg for msg in st.session_state.conversation_history if msg["role"] == "user"])
                message_question_index = len([msg for msg in st.session_state.conversation_history[:i+1] if msg["role"] == "user"])
                is_changeable = (message_question_index == user_messages_count)  # This is the response to the latest question
                
                feedback_html = f"""
                <div class="feedback-container">
                    <span class="feedback-text">Was this response helpful?</span>
                </div>
                """
                st.markdown(feedback_html, unsafe_allow_html=True)
                
                # columns: make the first three wider; last one is spacer
                col1, col2, col3, _spacer = st.columns([2.8, 2.8, 2.8, 3.6])

                with col1:
                    button_type = "primary" if current_feedback == "helpful" else "secondary"
                    if st.button("👍 Helpful", key=f"helpful_{i}",
                                help="This response was helpful" if is_changeable else "Feedback locked after new question",
                                type=button_type, disabled=not is_changeable, use_container_width=True):
                        handle_feedback(i, "helpful")

                with col2:
                    button_type = "primary" if current_feedback == "not_helpful" else "secondary"
                    if st.button("👎 Not Helpful", key=f"not_helpful_{i}",
                                help="This response was not helpful" if is_changeable else "Feedback locked after new question",
                                type=button_type, disabled=not is_changeable, use_container_width=True):
                        handle_feedback(i, "not_helpful")

                with col3:
                    button_type = "primary" if current_feedback == "partially_helpful" else "secondary"
                    if st.button("🤔 Partially", key=f"partial_{i}",
                                help="This response was partially helpful" if is_changeable else "Feedback locked after new question",
                                type=button_type, disabled=not is_changeable, use_container_width=True):
                        handle_feedback(i, "partially_helpful")

                
                # Show feedback status if already given
                if current_feedback:
                    if is_changeable:
                        feedback_text = {
                            "helpful": "✅ You found this helpful (click to change)",
                            "not_helpful": "❌ You found this not helpful (click to change)", 
                            "partially_helpful": "🤔 You found this partially helpful (click to change)"
                        }
                    else:
                        feedback_text = {
                            "helpful": "✅ Marked as helpful",
                            "not_helpful": "❌ Marked as not helpful", 
                            "partially_helpful": "🤔 Marked as partially helpful"
                        }
                    st.markdown(f"<small style='color: var(--muted);'>{feedback_text[current_feedback]}</small>", 
                              unsafe_allow_html=True)
                
                st.divider()
        
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_area(
                "Ask your question",
                placeholder="For example, how to calculate the moment about point A in a beam problem",
                height=100
            )
            col1, col2 = st.columns([1, 4])
            with col1:
                submit_button = st.form_submit_button("Ask ARIA", use_container_width=True)
            
            if submit_button and user_input:
                # Track new question - this will reset feedback changeability for previous responses
                current_question_count = len([msg for msg in st.session_state.conversation_history if msg["role"] == "user"])
                st.session_state.last_question_count = current_question_count + 1
                
                st.session_state.conversation_history.append({
                    "role": "user",
                    "content": user_input
                })
                with st.spinner("ARIA is thinking"):
                    try:
                        # Get session ID (create one if it doesn't exist)
                        if "session_id" not in st.session_state:
                            st.session_state.session_id = conversation_storage.create_session_id()
                        
                        start_time = time.time()
                        response_data = st.session_state.ta_system.generate_response(
                            user_input,
                            st.session_state.conversation_history[-10:]
                        )
                        response_time = time.time() - start_time
                        
                        # Store conversation in database and get conversation ID
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
        '<div class="app-footer"><div>Built by Dibakar Roy Sarkar and Yue Luo, © Centrum Intelliphysics Lab (PI: Somdatta Goswami),</div><div>Civil and System Engineering, Johns Hopkins University</div></div>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
