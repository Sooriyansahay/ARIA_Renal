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
    page_title="ARIA: Statics and Mechanics of Materials TA",
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

# Design CSS with CMU Serif everywhere
st.markdown("""
<style>
:root{
  --bg:#0c0c0d; --panel:#141416; --panel-2:#101113;
  --text:#e9e7e4; --muted:#b9b6b0; --border:#26272b;
  --accent:#6aa6ff; --accent-2:#9bbcff;
}

/* CMU Serif webfont declarations.
   If the files are present in ./fonts they will be used.
   Otherwise the local installed face will be used. */
@font-face{
  font-family:"CMU Serif";
  src: local("CMU Serif"), local("CMUSerif"),
       url("./fonts/cmunrm.woff2") format("woff2"),
       url("./fonts/cmunrm.woff") format("woff"),
       url("./fonts/cmunrm.ttf") format("truetype");
  font-weight:400; font-style:normal; font-display:swap;
}
@font-face{
  font-family:"CMU Serif";
  src: local("CMU Serif Bold"), local("CMUSerif-Bold"),
       url("./fonts/cmunbx.woff2") format("woff2"),
       url("./fonts/cmunbx.woff") format("woff"),
       url("./fonts/cmunbx.ttf") format("truetype");
  font-weight:700; font-style:normal; font-display:swap;
}
@font-face{
  font-family:"CMU Serif";
  src: local("CMU Serif Italic"), local("CMUSerif-Italic"),
       url("./fonts/cmunti.woff2") format("woff2"),
       url("./fonts/cmunti.woff") format("woff"),
       url("./fonts/cmunti.ttf") format("truetype");
  font-weight:400; font-style:italic; font-display:swap;
}
@font-face{
  font-family:"CMU Serif";
  src: local("CMU Serif Bold Italic"), local("CMUSerif-BoldItalic"),
       url("./fonts/cmunbi.woff2") format("woff2"),
       url("./fonts/cmunbi.woff") format("woff"),
       url("./fonts/cmunbi.ttf") format("truetype");
  font-weight:700; font-style:italic; font-display:swap;
}

/* Apply CMU Serif globally, including code blocks */
html, body, .stApp, .main, .block-container,
h1,h2,h3,h4,h5,h6,
p,div,span,label,li,small,em,strong,
button, input, textarea, select,
code, pre, kbd, samp {
  font-family: "CMU Serif", serif !important;
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
  background:var(--panel-2); color:var(--text); border:1px solid var(--border);
  border-radius:12px; padding:.75rem .9rem; transition:border .15s ease, box-shadow .15s ease;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stSelectbox > div > div > select:focus{
  border-color:var(--accent); box-shadow:0 0 0 3px rgba(106,166,255,.18); outline:none;
}

/* Buttons */
.stButton > button{
  background:var(--panel-2); color:var(--text); border:1px solid var(--border);
  border-radius:12px; padding:.7rem 1.1rem; font-weight:700;
  transition:transform .08s ease, background .15s ease, border .15s ease;
}
.stButton > button:hover{ background:#1b1d22; border-color:#30323a; transform:translateY(-1px); }

/* Single rail callout */
.aria-callout{
  position:relative; background:linear-gradient(135deg,#0f254a 0%,#0e1f3e 100%);
  border-radius:14px; padding:1.1rem 1.25rem; box-shadow:0 8px 24px rgba(0,0,0,.35), inset 0 0 0 1px rgba(255,255,255,.04);
}
.aria-callout::before{
  content:""; position:absolute; left:0; top:0; bottom:0; width:6px;
  background:var(--accent); border-top-left-radius:14px; border-bottom-left-radius:14px;
}

/* Messages */
.chat-message{
  padding:1.1rem 1.2rem; border-radius:12px; margin:1rem 0; border:1px solid var(--border);
  background:var(--panel); box-shadow:0 1px 6px rgba(0,0,0,.18);
}
.student-message{ background:#11151c; border-left:4px solid var(--accent); }
.ta-message{ background:#17121a; border-left:4px solid #a47aff; }

/* Feedback buttons */
.feedback-container{
  display:flex; align-items:center; gap:0.5rem; margin-top:0.75rem; padding-top:0.75rem;
  border-top:1px solid var(--border); opacity:0.8;
}
.feedback-text{
  font-size:0.85rem; color:var(--muted); margin-right:0.5rem;
}
.feedback-button{
  background:transparent; border:1px solid var(--border); border-radius:8px;
  padding:0.5rem 1rem; cursor:pointer; transition:all 0.15s ease;
  color:var(--muted); font-size:0.8rem; display:flex; align-items:center; gap:0.4rem;
  min-width:80px; white-space:nowrap;
}
.feedback-button:hover{
  background:var(--panel-2); border-color:var(--accent); color:var(--text);
}
.feedback-button.selected{
  background:var(--accent); border-color:var(--accent); color:white;
  transform:scale(1.05);
}
.feedback-button.selected.negative{
  background:#dc3545; border-color:#dc3545;
}
.feedback-button.selected.partial{
  background:#ffa500; border-color:#ffa500;
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

/* Light preference */
@media (prefers-color-scheme: light){
  :root{
    --bg:#faf9f7; --panel:#ffffff; --panel-2:#f7f7f9; --text:#2b2a28; --muted:#5d5b57; --border:#e6e4df;
    --accent:#3147c4; --accent-2:#5164de;
  }
  .stApp{ background:var(--bg); color:var(--text); }
  .main .block-container{ background:var(--bg); }
  .stButton > button{ background:var(--panel-2); }
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

def save_feedback_to_database(session_id, message_index, user_question, ai_response, feedback_type, concepts_covered=None, response_time=None):
    """Save feedback data to database"""
    try:
        success = feedback_storage.store_feedback(
            session_id=session_id,
            conversation_id=None,  # We can link this to conversation later if needed
            message_index=message_index,
            user_question=user_question,
            ai_response=ai_response,
            feedback_type=feedback_type,
            concepts_covered=concepts_covered or [],
            response_time=response_time
        )
        if not success:
            st.error("Failed to save feedback")
        return success
    except Exception as e:
        st.error(f"Error saving feedback: {e}")
        return False

def update_feedback_in_database(session_id, message_index, new_feedback_type):
    """Update existing feedback in database"""
    try:
        success = feedback_storage.update_feedback(
            session_id=session_id,
            message_index=message_index,
            new_feedback_type=new_feedback_type
        )
        if not success:
            st.error("Failed to update feedback")
        return success
    except Exception as e:
        st.error(f"Error updating feedback: {e}")
        return False

def delete_feedback_from_database(session_id, message_index):
    """Delete feedback from database"""
    try:
        success = feedback_storage.delete_feedback(
            session_id=session_id,
            message_index=message_index
        )
        return success
    except Exception as e:
        st.error(f"Error deleting feedback: {e}")
        return False

def handle_feedback(message_index, feedback_type):
    """Handle user feedback for a specific message"""
    if message_index < len(st.session_state.conversation_history):
        message = st.session_state.conversation_history[message_index]
        if message["role"] == "assistant":
            # Get session ID (create one if it doesn't exist)
            if "session_id" not in st.session_state:
                st.session_state.session_id = str(datetime.now().timestamp()).replace('.', '')
            
            session_id = st.session_state.session_id
            current_feedback = st.session_state.message_feedback.get(message_index)
            
            # Get user question and response details
            user_question = st.session_state.conversation_history[message_index-1]["content"] if message_index > 0 else ""
            ai_response = message["content"]
            concepts_covered = message.get("concepts", [])
            response_time = message.get("response_time", 0)
            
            # If clicking the same feedback type, remove it (toggle off)
            if current_feedback == feedback_type:
                # Remove feedback from database
                success = delete_feedback_from_database(session_id, message_index)
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
                # Check if feedback already exists for this message
                if current_feedback:
                    # Update existing feedback
                    success = update_feedback_in_database(session_id, message_index, feedback_type)
                else:
                    # Add new feedback
                    success = save_feedback_to_database(
                        session_id=session_id,
                        message_index=message_index,
                        user_question=user_question,
                        ai_response=ai_response,
                        feedback_type=feedback_type,
                        concepts_covered=concepts_covered,
                        response_time=response_time
                    )
                
                if success:
                    # Update session state
                    st.session_state.message_feedback[message_index] = feedback_type
                    
                    # Update feedback_data list (for backward compatibility)
                    feedback_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "message_index": message_index,
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
                st.success("TA system ready")
            else:
                st.error("Failed to initialize TA system. Check the API key.")
                return
    
    st.markdown(
        '<h1 class="app-title">ARIA: Statics and Mechanics of Materials TA</h1>',
        unsafe_allow_html=True
    )
    
    if st.session_state.system_initialized:
        st.markdown(
            """
            <div class="aria-callout">
              I am ARIA, your teaching assistant for Statics and Mechanics of Materials. I will guide you through problem solving steps and help you understand key concepts. How can I help you today
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
        
        # Supabase Database Status
        st.subheader("Database Status")
        if supabase_config.is_connected():
            st.success("✅ Supabase Connected")
            st.caption("Feedback data will be stored in Supabase database")
        else:
            st.warning("⚠️ Supabase Not Connected")
            st.caption("Feedback data will be stored locally in JSON files")
            with st.expander("How to configure Supabase"):
                st.markdown("""
                1. Create a Supabase project at [supabase.com](https://supabase.com)
                2. Go to Settings > API in your dashboard
                3. Copy your Project URL and anon key
                4. Add them to `.streamlit/secrets.toml`:
                ```toml
                SUPABASE_URL = "https://your-project-ref.supabase.co"
                SUPABASE_ANON_KEY = "your_anon_key_here"
                ```
                5. Restart the application
                """)
        
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
                        start_time = time.time()
                        response_data = st.session_state.ta_system.generate_response(
                            user_input,
                            st.session_state.conversation_history[-10:]
                        )
                        response_time = time.time() - start_time
                        ta_message = {
                            "role": "assistant",
                            "content": response_data["response"],
                            "concepts": response_data.get("concepts_covered", []),
                            "response_time": response_time
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
        '<p class="app-footer">Built by Dibakar Roy Sarkar and Yue Luo, Centrum IntelliPhysics Lab</p>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
