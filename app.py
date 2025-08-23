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

# Refined academic design with serif fonts
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Crimson+Text:ital,wght@0,400;0,600;0,700;1,400&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@300;400;500;600;700&display=swap');

/* Root variables for consistent theming */
:root {
    --primary-bg: #fafafa;
    --secondary-bg: #ffffff;
    --accent-bg: #f5f7fa;
    --primary-text: #2c3e50;
    --secondary-text: #5a6c7d;
    --accent-color: #3498db;
    --success-color: #27ae60;
    --warning-color: #f39c12;
    --error-color: #e74c3c;
    --border-color: #e1e8ed;
    --shadow-light: 0 2px 8px rgba(0, 0, 0, 0.08);
    --shadow-medium: 0 4px 16px rgba(0, 0, 0, 0.12);
    --border-radius: 8px;
    --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Global app styling */
.stApp {
    background-color: var(--primary-bg);
    color: var(--primary-text);
    font-family: 'Crimson Text', 'Times New Roman', serif;
    line-height: 1.7;
    font-size: 16px;
}

/* Enhanced sidebar with academic styling */
.css-1d391kg {
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    border-right: 2px solid var(--border-color);
    box-shadow: var(--shadow-medium);
}

/* Main content area refinements */
.main .block-container {
    background-color: var(--primary-bg);
    padding: 2.5rem 2rem;
    max-width: 1100px;
    margin: 0 auto;
}

/* Refined message containers with academic styling */
.chat-message {
    padding: 2rem;
    border-radius: var(--border-radius);
    margin: 2rem 0;
    border: 1px solid var(--border-color);
    background-color: var(--secondary-bg);
    color: var(--primary-text);
    box-shadow: var(--shadow-light);
    transition: var(--transition);
    font-size: 1.05rem;
    line-height: 1.8;
}

.chat-message:hover {
    box-shadow: var(--shadow-medium);
    transform: translateY(-2px);
}

/* Student message with refined styling */
.student-message {
    background: linear-gradient(135deg, #f8faff 0%, #ffffff 100%);
    border-left: 4px solid var(--accent-color);
    border-color: #e3f2fd;
    position: relative;
}

.student-message::before {
    content: "👤";
    position: absolute;
    top: 1rem;
    right: 1.5rem;
    font-size: 1.2rem;
    opacity: 0.6;
}

/* TA message with academic authority */
.ta-message {
    background: linear-gradient(135deg, #fdfbff 0%, #ffffff 100%);
    border-left: 4px solid #8e44ad;
    border-color: #f3e5f5;
    position: relative;
}

.ta-message::before {
    content: "🎓";
    position: absolute;
    top: 1rem;
    right: 1.5rem;
    font-size: 1.2rem;
    opacity: 0.6;
}

/* Enhanced input fields with academic styling */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background-color: var(--secondary-bg);
    color: var(--primary-text);
    border: 2px solid var(--border-color);
    border-radius: var(--border-radius);
    padding: 1rem;
    font-family: 'Crimson Text', 'Times New Roman', serif;
    font-size: 1.05rem;
    transition: var(--transition);
    box-shadow: var(--shadow-light);
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent-color);
    box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.15);
    outline: none;
    background-color: #fbfcfe;
}

/* Enhanced selectbox */
.stSelectbox > div > div > select {
    background-color: var(--secondary-bg);
    color: var(--primary-text);
    border: 2px solid var(--border-color);
    border-radius: var(--border-radius);
    padding: 1rem;
    font-family: 'Source Sans Pro', sans-serif;
    font-size: 0.95rem;
    transition: var(--transition);
    box-shadow: var(--shadow-light);
}

.stSelectbox > div > div > select:focus {
    border-color: var(--accent-color);
    box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.15);
}

/* Refined button styling */
.stButton > button {
    background: linear-gradient(135deg, var(--accent-color) 0%, #2980b9 100%);
    color: white;
    border: none;
    border-radius: var(--border-radius);
    padding: 0.875rem 2rem;
    font-family: 'Source Sans Pro', sans-serif;
    font-weight: 600;
    font-size: 0.95rem;
    transition: var(--transition);
    box-shadow: var(--shadow-light);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #2980b9 0%, #1f5f8b 100%);
    box-shadow: var(--shadow-medium);
    transform: translateY(-1px);
}

/* Secondary button variant */
.stButton > button[kind="secondary"] {
    background: transparent;
    color: var(--accent-color);
    border: 2px solid var(--accent-color);
}

.stButton > button[kind="secondary"]:hover {
    background-color: var(--accent-color);
    color: white;
}

/* Enhanced ARIA greeting */
.stAlert {
    background: linear-gradient(135deg, #e8f4fd 0%, #ffffff 100%);
    color: var(--primary-text);
    border: 2px solid #bde0ff;
    border-radius: 12px;
    padding: 2rem;
    box-shadow: var(--shadow-medium);
    margin: 2rem 0;
    position: relative;
}

.stAlert::before {
    content: "🤖";
    position: absolute;
    top: 1.5rem;
    right: 1.5rem;
    font-size: 1.5rem;
    opacity: 0.7;
}

/* Status messages with improved visibility */
.stSuccess {
    background: linear-gradient(135deg, #e8f8f5 0%, #ffffff 100%);
    color: #1e8449;
    border: 2px solid #a9dfbf;
    border-radius: var(--border-radius);
    padding: 1.5rem;
    box-shadow: var(--shadow-light);
    font-weight: 500;
}

.stError {
    background: linear-gradient(135deg, #fdedec 0%, #ffffff 100%);
    color: #c0392b;
    border: 2px solid #f1948a;
    border-radius: var(--border-radius);
    padding: 1.5rem;
    box-shadow: var(--shadow-light);
    font-weight: 500;
}

.stWarning {
    background: linear-gradient(135deg, #fef9e7 0%, #ffffff 100%);
    color: #b7950b;
    border: 2px solid #f7dc6f;
    border-radius: var(--border-radius);
    padding: 1.5rem;
    box-shadow: var(--shadow-light);
    font-weight: 500;
}

/* Enhanced metrics display */
.metric-container {
    background: linear-gradient(135deg, var(--secondary-bg) 0%, var(--accent-bg) 100%);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    padding: 1.5rem;
    box-shadow: var(--shadow-light);
    transition: var(--transition);
}

.metric-container:hover {
    box-shadow: var(--shadow-medium);
}

/* Form containers with academic styling */
.stForm {
    background: linear-gradient(135deg, var(--secondary-bg) 0%, #fafbfc 100%);
    border: 2px solid var(--border-color);
    border-radius: 12px;
    padding: 2rem;
    box-shadow: var(--shadow-medium);
    margin: 1.5rem 0;
}

/* Loading spinner */
.stSpinner {
    color: var(--accent-color);
}

/* Typography hierarchy with serif fonts */
h1, h2, h3, h4, h5, h6 {
    color: var(--primary-text) !important;
    font-family: 'Crimson Text', 'Times New Roman', serif !important;
    font-weight: 700 !important;
    line-height: 1.3 !important;
    margin: 1.5rem 0 1rem 0 !important;
    letter-spacing: -0.5px;
}

h1 { 
    font-size: 2.5rem !important;
    background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

h2 { 
    font-size: 2rem !important;
    color: #34495e !important;
    border-bottom: 2px solid var(--border-color);
    padding-bottom: 0.5rem;
}

h3 { 
    font-size: 1.6rem !important;
    color: #5a6c7d !important;
}

h4 { 
    font-size: 1.3rem !important;
    color: #7f8c8d !important;
}

/* Body text and labels */
p, div, span, label {
    color: var(--primary-text) !important;
    font-family: 'Crimson Text', 'Times New Roman', serif !important;
    font-weight: 400 !important;
    line-height: 1.7 !important;
}

/* Small text and captions */
.stCaption, .caption {
    font-family: 'Source Sans Pro', sans-serif !important;
    font-size: 0.85rem !important;
    color: var(--secondary-text) !important;
    font-style: italic;
}

/* Enhanced sidebar elements */
.css-1d391kg h1, 
.css-1d391kg h2, 
.css-1d391kg h3 {
    color: var(--primary-text) !important;
    border-bottom: 2px solid var(--border-color);
    padding-bottom: 0.75rem;
    margin-bottom: 1.5rem;
}

.css-1d391kg .stSubheader {
    color: #5a6c7d !important;
    font-weight: 600 !important;
    margin-top: 2rem !important;
}

/* List styling in sidebar */
.css-1d391kg ul {
    list-style: none;
    padding-left: 0;
}

.css-1d391kg li {
    padding: 0.5rem 0;
    border-bottom: 1px solid #f0f2f4;
    font-size: 0.95rem;
}

.css-1d391kg li::before {
    content: "→";
    color: var(--accent-color);
    margin-right: 0.5rem;
    font-weight: bold;
}

/* Refined dividers */
hr {
    border: none;
    height: 2px;
    background: linear-gradient(90deg, transparent 0%, var(--border-color) 20%, var(--border-color) 80%, transparent 100%);
    margin: 3rem 0;
}

/* Code blocks (if any) */
code {
    background-color: #f8f9fa;
    color: #e74c3c;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-size: 0.9rem;
    border: 1px solid #dee2e6;
}

/* Enhanced markdown content */
.markdown-text-container {
    color: var(--primary-text);
    line-height: 1.8;
    font-size: 1.05rem;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .main .block-container {
        padding: 1.5rem 1rem;
    }
    
    .chat-message {
        padding: 1.5rem;
        margin: 1.5rem 0;
    }
    
    h1 { font-size: 2rem !important; }
    h2 { font-size: 1.7rem !important; }
    h3 { font-size: 1.4rem !important; }
}

/* Focus indicators for accessibility */
*:focus {
    outline: 2px solid var(--accent-color);
    outline-offset: 2px;
}

/* Smooth scrolling */
html {
    scroll-behavior: smooth;
}

/* Selection styling */
::selection {
    background-color: rgba(52, 152, 219, 0.2);
    color: var(--primary-text);
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
    
    # Header with enhanced styling
    st.title("🔧 ARIA - Statics & Mechanics Teaching Assistant")
    
    # ARIA's personal introduction with enhanced styling
    if st.session_state.system_initialized:
        st.info("👋 **Welcome!** I'm ARIA, your AI Teaching Assistant for Statics & Mechanics of Materials. I'm designed to guide you through problem-solving steps and help you understand fundamental concepts. My goal is to help you learn by thinking, not by giving direct answers. How may I assist your learning journey today?")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # System status with enhanced display
        st.subheader("System Status")
        if st.session_state.system_initialized:
            st.success("✅ TA System Ready")
        else:
            st.error("❌ System Not Ready")
            
        # Topic filter with improved styling
        st.subheader("📚 Focus Area")
        topics = get_course_topics()
        selected_topic = st.selectbox(
            "Select a topic to focus on (optional):",
            ["All Topics"] + topics,
            help="Choose a specific area to concentrate our discussion"
        )
        
        # Conversation controls
        st.subheader("💬 Conversation")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Clear Chat", help="Start a new conversation"):
                st.session_state.conversation_history = []
                st.rerun()
        
        with col2:
            # Display conversation length
            conv_length = len(st.session_state.conversation_history)
            st.metric("Messages", conv_length)
        
        # Enhanced usage tips
        st.subheader("💡 Learning Tips")
        st.markdown("""
        **For effective learning with ARIA:**
        
        • **Ask specific questions** about concepts you're struggling with
        • **Describe your approach** so I can guide your thinking
        • **Request explanations** rather than direct solutions
        • **Ask for examples** to solidify understanding
        • **Inquire about common mistakes** to avoid pitfalls
        
        *Remember: The goal is understanding, not just answers!*
        """)
        
        # Quick help
        st.subheader("🚀 Quick Start")
        example_questions = [
            "How should I approach this truss analysis?",
            "What's the first step in beam deflection problems?",
            "Can you explain the concept of stress transformation?",
            "What assumptions do I make for rigid body analysis?"
        ]
        
        st.markdown("**Try asking:**")
        for i, question in enumerate(example_questions, 1):
            st.markdown(f"{i}. *{question}*")
    
    # Main chat interface
    if st.session_state.system_initialized and st.session_state.ta_system:
        # Display conversation history with enhanced styling
        if st.session_state.conversation_history:
            st.markdown("---")
            st.subheader("📝 Conversation History")
            
            for i, msg in enumerate(st.session_state.conversation_history):
                if msg["role"] == "user":
                    with st.container():
                        st.markdown(
                            f'<div class="chat-message student-message">'
                            f'<strong>You:</strong><br>{msg["content"]}'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                else:
                    with st.container():
                        st.markdown(
                            f'<div class="chat-message ta-message">'
                            f'<strong>ARIA:</strong><br>{msg["content"]}'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                        
                        # Display additional info if available
                        if "concepts" in msg and msg["concepts"]:
                            with st.expander("📖 Concepts Covered"):
                                st.write(", ".join(msg["concepts"]))
        
        # Enhanced chat input
        st.markdown("---")
        st.subheader("✏️ Ask ARIA")
        
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_area(
                "**Your question or problem:**",
                placeholder="Example: I'm working on a cantilever beam problem with a distributed load. How should I start setting up the equations for finding the maximum deflection?",
                height=120,
                help="Be specific about what you need help understanding or what step you're struggling with."
            )
            
            # Form submission
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                submit_button = st.form_submit_button(
                    "🚀 Ask ARIA", 
                    use_container_width=True,
                    type="primary"
                )
            with col2:
                if selected_topic != "All Topics":
                    st.markdown(f"*Focus: {selected_topic}*")
            
            if submit_button and user_input:
                # Add user message to history
                st.session_state.conversation_history.append({
                    "role": "user",
                    "content": user_input
                })
                
                # Generate TA response
                with st.spinner("🧠 ARIA is analyzing your question..."):
                    try:
                        start_time = time.time()
                        
                        # Add topic context if selected
                        enhanced_input = user_input
                        if selected_topic != "All Topics":
                            enhanced_input = f"[Context: {selected_topic}] {user_input}"
                        
                        response_data = st.session_state.ta_system.generate_response(
                            enhanced_input,
                            st.session_state.conversation_history[-10:]  # Last 10 messages
                        )
                        
                        response_time = time.time() - start_time
                        
                        # Add TA response to history
                        ta_message = {
                            "role": "assistant",
                            "content": response_data["response"],
                            "concepts": response_data.get("concepts_covered", []),
                            "response_time": response_time,
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        }
                        
                        st.session_state.conversation_history.append(ta_message)
                        
                        # Show performance metrics in sidebar
                        with st.sidebar:
                            st.markdown("---")
                            st.subheader("⚡ Performance")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Response Time", f"{response_time:.2f}s")
                            with col2:
                                st.metric("Last Update", ta_message["timestamp"])
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error generating response: {e}")
                        st.info("💡 Please try rephrasing your question or check your internet connection.")
    
    else:
        # Enhanced welcome message
        st.markdown("---")
        st.markdown("""
        ## 🎓 Welcome to Your Academic Companion!
        
        **ARIA** is your intelligent Teaching Assistant, specifically designed for Statics and Mechanics of Materials. 
        Unlike traditional homework helpers, ARIA focuses on **developing your problem-solving skills** through guided learning.
        
        ### 🌟 What Makes ARIA Special?
        
        **🎯 Pedagogical Approach:** ARIA will guide you through problems step-by-step, asking thought-provoking questions rather than providing direct answers.
        
        **📚 Deep Subject Knowledge:** Specialized understanding of statics, strength of materials, and structural analysis principles.
        
        **🤝 Adaptive Learning:** Adjusts explanations based on your level of understanding and learning progress.
        
        **💡 Conceptual Focus:** Emphasizes understanding fundamental principles that you can apply to various problems.
        
        ---
        
        ### 📖 Core Topics I Can Help With:
        """)
        
        # Display topics in a more attractive layout
        topics = get_course_topics()
        cols = st.columns(3)
        
        for i, topic in enumerate(topics):
            with cols[i % 3]:
                st.markdown(f"**• {topic}**")
        
        st.markdown("""
        ---
        
        ### 💬 Example Learning Conversations:
        
        **Instead of asking:** *"What's the answer to this truss problem?"*  
        **Try asking:** *"How do I determine if this truss is statically determinate?"*
        
        **Instead of asking:** *"Calculate the stress for me"*  
        **Try asking:** *"What factors should I consider when analyzing stress in this member?"*
        
        **Instead of asking:** *"Give me the formula"*  
        **Try asking:** *"Can you help me understand when to use this type of analysis?"*
        
        ---
        
        **🚀 The system is initializing... Please wait a moment.**
        """)
    
    # Enhanced attribution footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%); 
                   border-radius: 8px; border: 1px solid #e1e8ed; margin-top: 2rem;">
            <p style="margin: 0; font-style: italic; color: #5a6c7d;">
                <strong>Built with ❤️ by Dibakar Roy Sarkar and Yue Luo</strong><br>
                <em>Centrum IntelliPhysics Lab • Academic Excellence Through AI</em>
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
