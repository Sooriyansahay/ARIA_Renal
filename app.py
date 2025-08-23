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
    page_title="ARIA: Statics and Mechanics of Materials TA",
    layout="wide",
    initial_sidebar_state="expanded"
)

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


# Session state
if "ta_system" not in st.session_state:
    st.session_state.ta_system = None
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "system_initialized" not in st.session_state:
    st.session_state.system_initialized = False

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
