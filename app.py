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

# Enhanced minimal dark theme CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Dark background for entire app */
.stApp {
    background-color: #0a0a0a;
    color: #e8e8e8;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    line-height: 1.6;
}

/* Enhanced sidebar */
.css-1d391kg {
    background-color: #111111;
    border-right: 1px solid #2a2a2a;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.3);
}

/* Enhanced main content area */
.main .block-container {
    background-color: #0a0a0a;
    color: #e8e8e8;
    padding: 2rem 1.5rem;
    max-width: 1200px;
}

/* Enhanced message containers */
.chat-message {
    padding: 1.5rem;
    border-radius: 12px;
    margin: 1.5rem 0;
    border: 1px solid #2a2a2a;
    background-color: #141414;
    color: #e8e8e8;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    transition: all 0.2s ease;
    font-weight: 400;
    line-height: 1.7;
}

.chat-message:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    transform: translateY(-1px);
}

/* Enhanced student message styling */
.student-message {
    background-color: #0f1419;
    border-left: 4px solid #3b82f6;
    color: #e8e8e8;
    border-color: #1e3a8a;
}

/* Enhanced TA message styling */
.ta-message {
    background-color: #1a0f1a;
    border-left: 4px solid #a855f7;
    color: #e8e8e8;
    border-color: #581c87;
}

/* Enhanced input fields */
.stTextInput > div > div > input {
    background-color: #1a1a1a;
    color: #e8e8e8;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 0.75rem;
    font-family: 'Inter', sans-serif;
    font-weight: 400;
    transition: all 0.2s ease;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.stTextInput > div > div > input:focus {
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    outline: none;
}

.stTextArea > div > div > textarea {
    background-color: #1a1a1a;
    color: #e8e8e8;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 0.75rem;
    font-family: 'Inter', sans-serif;
    font-weight: 400;
    line-height: 1.6;
    transition: all 0.2s ease;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.stTextArea > div > div > textarea:focus {
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    outline: none;
}

/* Enhanced selectbox */
.stSelectbox > div > div > select {
    background-color: #1a1a1a;
    color: #e8e8e8;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 0.75rem;
    font-family: 'Inter', sans-serif;
    font-weight: 400;
    transition: all 0.2s ease;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Enhanced buttons */
.stButton > button {
    background-color: #1a1a1a;
    color: #e8e8e8;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 0.75rem 1.5rem;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    transition: all 0.2s ease;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.stButton > button:hover {
    background-color: #2a2a2a;
    border-color: #3a3a3a;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
    transform: translateY(-1px);
}

/* Enhanced ARIA greeting box */
.stAlert {
    background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
    color: #e8e8e8;
    border: 1px solid #3b82f6;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 4px 12px rgba(30, 58, 138, 0.2);
    font-weight: 400;
    line-height: 1.6;
}

/* Enhanced success/error messages */
.stSuccess {
    background-color: #0f5132;
    color: #e8e8e8;
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 2px 6px rgba(15, 81, 50, 0.2);
    border: 1px solid #16a34a;
}

.stError {
    background-color: #721c24;
    color: #e8e8e8;
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 2px 6px rgba(114, 28, 36, 0.2);
    border: 1px solid #dc2626;
}

/* Enhanced metrics */
.metric-container {
    background-color: #1a1a1a;
    color: #e8e8e8;
    border-radius: 8px;
    padding: 1rem;
    border: 1px solid #2a2a2a;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Enhanced form containers */
.stForm {
    background-color: #141414;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Enhanced spinner */
.stSpinner {
    color: #3b82f6;
}

/* Enhanced typography */
h1, h2, h3, h4, h5, h6 {
    color: #f8fafc !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    line-height: 1.3 !important;
    margin-bottom: 1rem !important;
}

h1 { font-size: 2.25rem !important; }
h2 { font-size: 1.875rem !important; }
h3 { font-size: 1.5rem !important; }
h4 { font-size: 1.25rem !important; }

p, div, span, label {
    color: #e8e8e8 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 400 !important;
}

/* Enhanced markdown content */
.markdown-text-container {
    color: #e8e8e8;
    line-height: 1.7;
}

/* Enhanced sidebar elements */
.css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3 {
    color: #f8fafc !important;
    border-bottom: 1px solid #2a2a2a;
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
}

/* Clean dividers */
hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, #2a2a2a, transparent);
    margin: 2rem 0;
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
    st.title("🔧 ARIA - Statics & Mechanics Teaching Assistant")
    
    # ARIA's personal introduction
    if st.session_state.system_initialized:
        st.info("👋 Hi! I'm ARIA - Your AI Teaching Assistant for Statics & Mechanics of Materials. I'm here to guide you through problem-solving steps and help you understand key concepts. How can I help you today?")
    
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
        • Ask specific questions about concepts
        • Describe your problem step by step
        • Ask for guidance, not direct answers
        • Request examples or analogies
        • Ask about common mistakes to avoid
        """)
        

    
    # Main chat interface
    if st.session_state.system_initialized and st.session_state.ta_system:
        # Display conversation history
        for i, msg in enumerate(st.session_state.conversation_history):
            if msg["role"] == "user":
                with st.container():
                    st.write(f"**You:** {msg['content']}")
            else:
                with st.container():
                    st.write(f"**ARIA:** {msg['content']}")
                    st.divider()
                

        
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
    st.divider()
    st.caption("Built by Dibakar Roy Sarkar and Yue Luo - Centrum IntelliPhysics Lab")

if __name__ == "__main__":
    main()