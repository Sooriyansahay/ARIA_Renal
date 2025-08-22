import streamlit as st
import sys
import os
from pathlib import Path

# Add the parent directory to the path to import scripts
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
    color: #1f77b4;
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
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Chat interface
        st.subheader("💬 Chat with ARIA")
        
        # Display conversation history
        for i, (question, response) in enumerate(st.session_state.conversation_history):
            # Student question
            st.markdown(f"""
            <div class="chat-message student-message">
                <strong>🎓 You:</strong> {question}
            </div>
            """, unsafe_allow_html=True)
            
            # TA response
            st.markdown(f"""
            <div class="chat-message ta-message">
                <strong>🤖 ARIA:</strong> {response}
            </div>
            """, unsafe_allow_html=True)
        
        # Question input
        question = st.text_area(
            "Ask ARIA a question about Statics & Mechanics:",
            height=100,
            placeholder="e.g., How do I calculate the moment about point A in this truss problem?"
        )
        
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        
        with col_btn1:
            if st.button("Ask ARIA", type="primary"):
                if question and st.session_state.system_initialized:
                    with st.spinner("ARIA is thinking..."):
                        try:
                            response = st.session_state.ta_system.get_response(question)
                            st.session_state.conversation_history.append((question, response))
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error getting response: {e}")
                elif not question:
                    st.warning("Please enter a question first.")
        
        with col_btn2:
            if st.button("Clear Chat"):
                st.session_state.conversation_history = []
                st.rerun()
    
    with col2:
        # Sidebar content
        st.subheader("📚 Course Topics")
        topics = get_course_topics()
        
        st.markdown("**Available Topics:**")
        for topic in topics:
            st.markdown(f"• {topic}")
        
        st.markdown("---")
        
        st.subheader("💡 Tips for Better Learning")
        st.markdown("""
        • Ask specific questions about problems
        • Request step-by-step explanations
        • Ask for concept clarifications
        • Request practice problems
        • Ask about real-world applications
        """)
        
        st.markdown("---")
        
        st.subheader("🔧 System Status")
        if st.session_state.system_initialized:
            st.success("✅ ARIA is ready")
            st.info(f"💬 {len(st.session_state.conversation_history)} conversations")
        else:
            st.error("❌ System not initialized")
    
    # Footer with attribution
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem; padding: 1rem;">
        <p><strong>ARIA Teaching Assistant</strong> | Developed by <strong>Dibakar Roy Sarkar</strong> and <strong>Yue Luo</strong></p>
        <p>Centrum IntelliPhysics Lab | Powered by Advanced AI & RAG Technology</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()