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

# No custom CSS - using standard Streamlit styling only

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