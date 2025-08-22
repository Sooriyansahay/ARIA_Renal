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
except:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        st.error("OpenAI API key not found. Please set it in Streamlit secrets or environment variables.")
        st.stop()

# Page configuration
st.set_page_config(
    page_title="ARIA - Statics & Mechanics TA",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better performance and appearance
st.markdown("""
<style>
/* Main header styling */
.main-header {
    font-size: 2.5rem;
    color: #ffffff;
    text-align: center;
    margin-bottom: 2rem;
    font-weight: bold;
}

/* Chat message containers */
.chat-message {
    padding: 1.2rem;
    border-radius: 0.8rem;
    margin: 1rem 0;
    border-left: 5px solid #1f77b4;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    color: #2c3e50;
    font-size: 1rem;
    line-height: 1.6;
}

/* Student message styling */
.student-message {
    background-color: #ffffff;
    border: 2px solid #ff7f0e;
    border-left: 5px solid #ff7f0e;
    color: #2c3e50;
}

/* TA message styling */
.ta-message {
    background-color: #f8f9fa;
    border: 2px solid #1f77b4;
    border-left: 5px solid #1f77b4;
    color: #2c3e50;
}

/* Streamlit input styling */
.stTextArea > div > div > textarea {
    background-color: #ffffff !important;
    color: #2c3e50 !important;
    border: 2px solid #bdc3c7 !important;
    border-radius: 0.5rem !important;
    font-size: 1rem !important;
}

.stTextArea > div > div > textarea:focus {
    border-color: #1f77b4 !important;
    box-shadow: 0 0 0 2px rgba(31, 119, 180, 0.2) !important;
}

/* Button styling */
.stButton > button {
    background-color: #1f77b4 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 0.5rem !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.2rem !important;
    font-size: 1rem !important;
}

.stButton > button:hover {
    background-color: #1565c0 !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
}

/* Sidebar styling */
.css-1d391kg {
    background-color: #2c3e50 !important;
}

/* Sidebar text styling - make text white for better visibility */
.css-1d391kg .stMarkdown, 
.css-1d391kg .stText,
.css-1d391kg h1,
.css-1d391kg h2,
.css-1d391kg h3,
.css-1d391kg p,
.css-1d391kg li,
.css-1d391kg ul,
.css-1d391kg ol {
    color: #ffffff !important;
}

/* Force white color for all sidebar content */
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stText,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] li,
[data-testid="stSidebar"] ul,
[data-testid="stSidebar"] ol {
    color: #ffffff !important;
}

/* General text contrast improvements */
.stMarkdown, .stText {
    color: #2c3e50 !important;
}

/* Success/Error message styling */
.stSuccess {
    background-color: #d4edda !important;
    color: #155724 !important;
    border: 1px solid #c3e6cb !important;
}

.stError {
    background-color: #f8d7da !important;
    color: #721c24 !important;
    border: 1px solid #f5c6cb !important;
}

/* Selectbox styling */
.stSelectbox > div > div {
    background-color: #ffffff !important;
    color: #2c3e50 !important;
    border: 2px solid #bdc3c7 !important;
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
        with st.spinner("Initializing TA system..."):
            ta_system = initialize_ta_system()
            if ta_system:
                st.session_state.ta_system = ta_system
                st.session_state.system_initialized = True
                st.success("TA system ready!", icon="✅")
            else:
                st.error("Failed to initialize TA system. Please check the API key.")
                return
    
    # Header
    st.markdown('<h1 class="main-header">🔧 ARIA - Statics & Mechanics Teaching Assistant</h1>', unsafe_allow_html=True)
    
    # ARIA's personal introduction
    if st.session_state.system_initialized:
        st.markdown("""
        <div style="background-color: #e3f2fd; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; border-left: 4px solid #1f77b4;">
            <h3 style="color: #1f77b4; margin: 0 0 0.5rem 0;">👋 Hi! I'm ARIA</h3>
            <p style="margin: 0; color: #2c3e50;">Your AI Teaching Assistant for Statics & Mechanics of Materials. I'm here to guide you through problem-solving steps and help you understand key concepts. How can I help you today?</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # System status
        if st.session_state.system_initialized:
            st.success("✅ TA System Ready")
        else:
            st.error("❌ System Not Ready")
            
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
        st.subheader("💡 Tips for Better Learning")
        st.markdown("""
        <div style="color: white !important;">
        • Ask specific questions about concepts<br>
        • Describe your problem step by step<br>
        • Ask for guidance, not direct answers<br>
        • Request examples or analogies<br>
        • Ask about common mistakes to avoid
        </div>
        """, unsafe_allow_html=True)
        

    
    # Main chat interface
    if st.session_state.system_initialized and st.session_state.ta_system:
        # Display conversation history
        for i, msg in enumerate(st.session_state.conversation_history):
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="chat-message student-message"><strong>You:</strong> {msg["content"]}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="chat-message ta-message"><strong>ARIA:</strong> {msg["content"]}</div>',
                    unsafe_allow_html=True
                )
                

        
        # Chat input
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_area(
                "Ask your question:",
                placeholder="e.g., How do I approach calculating the moment about point A in this beam problem?",
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
                with st.spinner("ARIA is thinking..."):
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
        ## Welcome to your Statics & Mechanics Teaching Assistant! 🎓
        
        This AI-powered TA is designed to help you learn by:
        - **Guiding** you through problem-solving steps
        - **Explaining** key concepts and formulas
        - **Providing** hints and examples
        - **Asking** questions to check your understanding
        
        **Important:** This TA will NOT give you direct answers. Instead, it will help you develop problem-solving skills!
        
        The system is initializing automatically...
        """)
        
        # Example questions
        st.subheader("Example Questions You Can Ask:")
        examples = [
            "How do I start analyzing a truss structure?",
            "What's the difference between stress and strain?",
            "Can you guide me through setting up equilibrium equations?",
            "What are the key steps for calculating beam deflections?",
            "How do I determine if a structure is statically determinate?"
        ]
        
        for example in examples:
            st.markdown(f"• {example}")
    
    # Attribution footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #7f8c8d; font-size: 0.8rem; margin-top: 2rem;">
            Built by <strong>Dibakar Roy Sarkar</strong> and <strong>Yue Luo</strong><br>
            <em>Centrum IntelliPhysics Lab</em>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()