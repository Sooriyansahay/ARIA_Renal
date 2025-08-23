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
    page_title="ARIA Statics and Mechanics TA",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Minimal dark theme with serif typography similar to CMU Serif or Times New Roman
st.markdown("""
<style>
:root{
  --bg: #0c0c0d;
  --panel: #141416;
  --panel-2: #101113;
  --text: #e9e7e4;
  --muted: #b9b6b0;
  --border: #26272b;
  --accent: #7f93ff;
  --accent-2: #9aa8ff;
  --success: #19b36b;
  --danger: #e24a4a;
}

/* Prefer a serif stack similar to CMU Serif or Times New Roman if available */
@font-face{
  font-family: "CMU Serif";
  src: local("CMU Serif");
  font-display: swap;
}

.stApp{
  background-color: var(--bg);
  color: var(--text);
  font-family: "CMU Serif", "Times New Roman", Times, Georgia, Cambria, "Liberation Serif", serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Main content width and comfortable reading rhythm */
.main .block-container{
  max-width: 960px;
  padding: 2rem 1.5rem;
  background: var(--bg);
}

/* Headings */
h1, h2, h3, h4, h5, h6{
  color: var(--text) !important;
  font-weight: 600 !important;
  letter-spacing: 0.2px !important;
  line-height: 1.25 !important;
  margin: 0 0 0.8rem 0 !important;
}
h1{ font-size: 2.1rem !important; }
h2{ font-size: 1.7rem !important; }
h3{ font-size: 1.35rem !important; }
h4{ font-size: 1.15rem !important; }

/* Body copy tuned for long reading */
p, div, span, label, li{
  color: var(--text) !important;
  font-weight: 400 !important;
  font-size: 16.5px !important;
  line-height: 1.75 !important;
}

/* Links with gentle accent */
a, a:visited{
  color: var(--accent);
  text-decoration: none;
}
a:hover{
  color: var(--accent-2);
  text-decoration: underline;
}

/* Sidebar using stable selector */
[data-testid="stSidebar"]{
  background: var(--panel);
  border-right: 1px solid var(--border);
  box-shadow: 2px 0 8px rgba(0,0,0,0.25);
  padding-top: 0.5rem;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3{
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.5rem;
  margin-bottom: 0.75rem;
}

/* Form fields */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > select{
  background: var(--panel-2);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.75rem 0.9rem;
  transition: border 0.15s ease, box-shadow 0.15s ease;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stSelectbox > div > div > select:focus{
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(127,147,255,0.18);
  outline: none;
}

/* Buttons */
.stButton > button{
  background: var(--panel-2);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.7rem 1.1rem;
  font-weight: 600;
  transition: transform 0.08s ease, background 0.15s ease, border 0.15s ease;
}
.stButton > button:hover{
  background: #1b1d22;
  border-color: #30323a;
  transform: translateY(-1px);
}

/* Alert and status blocks */
.stAlert{
  background: linear-gradient(135deg, #182145 0%, #111842 100%);
  color: var(--text);
  border: 1px solid #2b3a7a;
  border-radius: 12px;
  padding: 1.2rem 1.25rem;
}
.stSuccess{
  background: #0f2a1f;
  color: var(--text);
  border: 1px solid #1f7a52;
  border-radius: 10px;
  padding: 0.9rem 1rem;
}
.stError{
  background: #2a1416;
  color: var(--text);
  border: 1px solid #7a2b2b;
  border-radius: 10px;
  padding: 0.9rem 1rem;
}

/* Metrics */
.metric-container{
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: 10px;
  color: var(--text);
  padding: 1rem;
}

/* Forms and sections */
.stForm{
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.25rem;
}

/* Divider */
hr{
  border: none;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--border), transparent);
  margin: 1.75rem 0;
}

/* Conversation styling */
.chat-message{
  padding: 1.15rem 1.2rem;
  border-radius: 12px;
  margin: 1rem 0;
  border: 1px solid var(--border);
  background: var(--panel);
  box-shadow: 0 1px 6px rgba(0,0,0,0.18);
}
.student-message{
  background: #12161c;
  border-left: 4px solid #6ea3ff;
}
.ta-message{
  background: #17121a;
  border-left: 4px solid #a47aff;
}

/* Code blocks */
code, pre code{
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace !important;
  font-size: 14px !important;
}
pre{
  background: #0f1012 !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  padding: 1rem !important;
  overflow-x: auto !important;
}

/* Respect OS light preference */
@media (prefers-color-scheme: light){
  :root{
    --bg: #faf9f7;
    --panel: #ffffff;
    --panel-2: #f7f7f9;
    --text: #2b2a28;
    --muted: #5d5b57;
    --border: #e6e4df;
    --accent: #3147c4;
    --accent-2: #5164de;
  }
  .stApp{ background: var(--bg); color: var(--text); }
  .main .block-container{ background: var(--bg); }
  a, a:visited{ color: var(--accent); }
  .stButton > button{ background: var(--panel-2); }
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "ta_system" not in st.session_state:
    st.session_state.ta_system = None
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "system_initialized" not in st.session_state:
    st.session_state.system_initialized = False

def initialize_ta_system():
    """Initialize the TA system with API key from environment"""
    try:
        base_path = str(Path(__file__).parent)
        ta_system = StaticsMechanicsTA(base_path, OPENAI_API_KEY)
        return ta_system
    except Exception as e:
        st.error(f"Failed to initialize TA system: {e}")
        return None

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_course_topics():
    """Get available course topics for filtering"""
    topics = [
        "Rigid Body Equilibrium", "Force Systems", "Moments", "Trusses",
        "Frames and Machines", "Stress and Strain", "Axial Force Members",
        "Torsion", "Bending", "Shear", "Deflections", "Centroids",
        "Moment of Inertia", "Stress Transformation", "Principal Stresses"
    ]
    return topics

def main():
    # Auto-initialize TA system on first load
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
    
    # Header
    st.title("ARIA Statics and Mechanics Teaching Assistant")
    
    # ARIA introduction
    if st.session_state.system_initialized:
        st.info("I am ARIA, your teaching assistant for Statics and Mechanics of Materials. I will guide you through problem solving steps and help you understand key concepts. How can I help you today")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # System status
        if st.session_state.system_initialized:
            st.success("TA System Ready")
        else:
            st.error("System Not Ready")
            
        # Topic filter
        st.subheader("Focus Area")
        topics = get_course_topics()
        selected_topic = st.selectbox(
            "Select a topic to focus on (optional)",
            ["All Topics"] + topics
        )
        
        # Conversation controls
        st.subheader("Conversation")
        if st.button("Clear Conversation"):
            st.session_state.conversation_history = []
            st.rerun()
        
        # Usage tips
        st.subheader("Tips for Better Learning")
        st.markdown("""
        • Ask specific questions about concepts  
        • Describe your problem step by step  
        • Ask for guidance, not direct answers  
        • Request examples or analogies  
        • Ask about common mistakes to avoid
        """)
        
    # Main chat interface
    if st.session_state.system_initialized and st.session_state.ta_system:
        # Display conversation history with styled blocks
        for msg in st.session_state.conversation_history:
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="chat-message student-message"><strong>You</strong><br>{msg["content"]}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="chat-message ta-message"><strong>ARIA</strong><br>{msg["content"]}</div>',
                    unsafe_allow_html=True
                )
                st.divider()
        
        # Chat input
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
                # Add user message to history
                st.session_state.conversation_history.append({
                    "role": "user",
                    "content": user_input
                })
                
                # Generate TA response
                with st.spinner("ARIA is thinking"):
                    try:
                        start_time = time.time()
                        
                        response_data = st.session_state.ta_system.generate_response(
                            user_input,
                            st.session_state.conversation_history[-10:]  # Last 10 messages
                        )
                        
                        response_time = time.time() - start_time
                        
                        # Add TA response to history
                        ta_message = {
                            "role": "assistant",
                            "content": response_data["response"],
                            "concepts": response_data.get("concepts_covered", []),
                            "response_time": response_time
                        }
                        
                        st.session_state.conversation_history.append(ta_message)
                        
                        # Show performance metrics in sidebar
                        with st.sidebar:
                            st.metric("Response Time", f"{response_time:.2f}s")
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error generating response: {e}")
    
    else:
        # Welcome message
        st.markdown("""
        ## Welcome to your Statics and Mechanics Teaching Assistant
        
        This assistant helps you learn by  
        • Guiding you through problem solving steps  
        • Explaining key concepts and formulas  
        • Providing hints and examples  
        • Asking questions to check your understanding
        
        Important  
        This assistant will not give direct answers. It will help you develop problem solving skills.
        
        The system initializes automatically.
        """)
        
        # Example questions
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
    
    # Attribution footer
    st.divider()
    st.caption("Built by Dibakar Roy Sarkar and Yue Luo, Centrum IntelliPhysics Lab")

if __name__ == "__main__":
    main()
