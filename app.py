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

# Custom CSS for beautiful modern theme
st.markdown("""
<style>
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* Modern gradient background */
.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
}

/* Glassmorphism main container */
.main .block-container {
    background: rgba(255, 255, 255, 0.1) !important;
    backdrop-filter: blur(20px) !important;
    border-radius: 20px !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
    color: #ffffff !important;
    padding: 2rem !important;
    margin: 1rem !important;
    animation: fadeInUp 0.8s ease-out !important;
}

/* Animated main header */
.main-header {
    font-size: 3rem;
    color: #ffffff !important;
    text-align: center;
    margin-bottom: 2rem;
    font-weight: 700;
    font-family: 'Inter', sans-serif !important;
    background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4, #feca57);
    background-size: 300% 300%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: gradientShift 4s ease-in-out infinite, textGlow 2s ease-in-out infinite alternate;
    text-shadow: 0 0 30px rgba(255, 255, 255, 0.5);
}

/* Keyframe animations */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

@keyframes textGlow {
    from { text-shadow: 0 0 20px rgba(255, 255, 255, 0.5); }
    to { text-shadow: 0 0 30px rgba(255, 255, 255, 0.8), 0 0 40px rgba(255, 255, 255, 0.3); }
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateX(-20px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}

/* Modern glassmorphism chat containers */
.chat-message {
    padding: 1.5rem;
    border-radius: 20px;
    margin: 1.5rem 0;
    backdrop-filter: blur(15px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    color: #ffffff;
    font-size: 1.1rem;
    line-height: 1.7;
    font-family: 'Inter', sans-serif;
    animation: slideIn 0.5s ease-out;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.chat-message::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #ff6b6b, #4ecdc4, #45b7d1);
    background-size: 200% 100%;
    animation: gradientShift 3s ease-in-out infinite;
}

.chat-message:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3);
}

/* Student message with warm gradient */
.student-message {
    background: linear-gradient(135deg, rgba(255, 107, 107, 0.2), rgba(255, 202, 87, 0.2));
    border-left: 4px solid #ff6b6b;
}

/* TA message with cool gradient */
.ta-message {
    background: linear-gradient(135deg, rgba(69, 183, 209, 0.2), rgba(78, 205, 196, 0.2));
    border-left: 4px solid #45b7d1;
}

/* Modern glassmorphism inputs */
.stTextArea > div > div > textarea {
    background: rgba(255, 255, 255, 0.1) !important;
    backdrop-filter: blur(10px) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 15px !important;
    font-size: 1.1rem !important;
    font-family: 'Inter', sans-serif !important;
    padding: 1rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
}

.stTextArea > div > div > textarea:focus {
    border-color: rgba(102, 126, 234, 0.6) !important;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2), 0 8px 25px rgba(0, 0, 0, 0.15) !important;
    transform: translateY(-2px) !important;
}

.stTextArea > div > div > textarea::placeholder {
    color: rgba(255, 255, 255, 0.6) !important;
    font-style: italic !important;
}

/* Modern gradient buttons */
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 15px !important;
    font-weight: 600 !important;
    padding: 0.8rem 2rem !important;
    font-size: 1.1rem !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    position: relative !important;
    overflow: hidden !important;
}

.stButton > button::before {
    content: '' !important;
    position: absolute !important;
    top: 0 !important;
    left: -100% !important;
    width: 100% !important;
    height: 100% !important;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent) !important;
    transition: left 0.5s !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
    transform: translateY(-3px) scale(1.05) !important;
    box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4) !important;
}

.stButton > button:hover::before {
    left: 100% !important;
}

.stButton > button:active {
    transform: translateY(-1px) scale(1.02) !important;
}

/* Sidebar styling for dark theme */
.css-1d391kg {
    background-color: #1a1a1a !important;
}

/* Sidebar text styling */
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

/* Glassmorphism sidebar */
.css-1d391kg {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05)) !important;
    backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.2) !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05)) !important;
    backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.2) !important;
}

/* Sidebar content styling */
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
    font-family: 'Inter', sans-serif !important;
}

/* Sidebar headers with gradient */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    background: linear-gradient(45deg, #ff6b6b, #4ecdc4) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    font-weight: 600 !important;
}

/* Enhanced typography */
.stMarkdown, .stText {
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    line-height: 1.6 !important;
}

/* Beautiful text hierarchy */
h1, h2, h3, h4, h5, h6 {
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    margin-bottom: 1rem !important;
}

p, span, div {
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
}

/* Code styling */
code {
    background: rgba(255, 255, 255, 0.1) !important;
    color: #ff6b6b !important;
    padding: 0.2rem 0.4rem !important;
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.9rem !important;
}

pre {
    background: rgba(255, 255, 255, 0.1) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* Links styling */
a {
    color: #4ecdc4 !important;
    text-decoration: none !important;
    transition: all 0.3s ease !important;
}

a:hover {
    color: #45b7d1 !important;
    text-shadow: 0 0 10px rgba(78, 205, 196, 0.5) !important;
}

/* Success/Error messages with modern styling */
.stSuccess {
    background: linear-gradient(135deg, rgba(76, 175, 80, 0.2), rgba(139, 195, 74, 0.2)) !important;
    backdrop-filter: blur(10px) !important;
    color: #ffffff !important;
    border: 1px solid rgba(76, 175, 80, 0.3) !important;
    border-radius: 12px !important;
    font-family: 'Inter', sans-serif !important;
}

.stError {
    background: linear-gradient(135deg, rgba(244, 67, 54, 0.2), rgba(233, 30, 99, 0.2)) !important;
    backdrop-filter: blur(10px) !important;
    color: #ffffff !important;
    border: 1px solid rgba(244, 67, 54, 0.3) !important;
    border-radius: 12px !important;
    font-family: 'Inter', sans-serif !important;
}

/* Modern form elements */
.stSelectbox > div > div {
    background: rgba(255, 255, 255, 0.1) !important;
    backdrop-filter: blur(10px) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 12px !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.3s ease !important;
}

.stSelectbox > div > div:hover {
    border-color: rgba(102, 126, 234, 0.6) !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
}

.stNumberInput > div > div > input {
    background: rgba(255, 255, 255, 0.1) !important;
    backdrop-filter: blur(10px) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 12px !important;
    font-family: 'Inter', sans-serif !important;
}

/* Glassmorphism metrics */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05)) !important;
    backdrop-filter: blur(15px) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 15px !important;
    color: #ffffff !important;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1) !important;
    transition: transform 0.3s ease !important;
}

[data-testid="metric-container"]:hover {
    transform: translateY(-3px) !important;
}

/* Modern expanders */
.streamlit-expanderHeader {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05)) !important;
    backdrop-filter: blur(10px) !important;
    color: #ffffff !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
}

.streamlit-expanderContent {
    background: rgba(255, 255, 255, 0.05) !important;
    backdrop-filter: blur(10px) !important;
    color: #ffffff !important;
    border-radius: 0 0 12px 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-top: none !important;
}

/* Spinner styling */
.stSpinner {
    color: #667eea !important;
}

/* Custom scrollbar */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #764ba2, #667eea);
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
        <div style="
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.3), rgba(118, 75, 162, 0.3));
            backdrop-filter: blur(20px);
            padding: 2rem;
            border-radius: 20px;
            margin-bottom: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            position: relative;
            overflow: hidden;
            animation: pulse 3s ease-in-out infinite;
        ">
            <div style="
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: linear-gradient(90deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4);
                background-size: 300% 100%;
                animation: gradientShift 3s ease-in-out infinite;
            "></div>
            <h3 style="
                color: #ffffff;
                margin: 0 0 1rem 0;
                font-size: 1.8rem;
                font-weight: 600;
                font-family: 'Inter', sans-serif;
                background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            ">👋 Hi! I'm ARIA</h3>
            <p style="
                margin: 0;
                color: rgba(255, 255, 255, 0.9);
                font-size: 1.1rem;
                line-height: 1.6;
                font-family: 'Inter', sans-serif;
            ">Your AI Teaching Assistant for Statics & Mechanics of Materials. I'm here to guide you through problem-solving steps and help you understand key concepts. How can I help you today? ✨</p>
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