import streamlit as st
import utils
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="UPSC Prep Mate", layout="wide", page_icon="🇮🇳")

# --- SESSION STATE MANAGEMENT ---
if "page" not in st.session_state:
    st.session_state.page = "home"
if "language" not in st.session_state:
    st.session_state.language = "English"
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "answers" not in st.session_state:
    st.session_state.answers = {}

# --- HELPER: LANGUAGE TEXT ---
TRANS = {
    "English": {
        "title": "UPSC Prelims Master",
        "pyq_btn": "Attempt PYQs",
        "quiz_btn": "Take Custom Quiz",
        "settings": "Settings",
        "gen_btn": "Generate Quiz",
        "loading": "System 1 Fetching... System 2 Verifying...",
        "submit": "Submit Quiz",
        "home": "Home"
    },
    "Hindi": {
        "title": "UPSC प्रारंभिक परीक्षा मास्टर",
        "pyq_btn": "पिछले वर्षों के प्रश्न (PYQ)",
        "quiz_btn": "कस्टम क्विज़ लें",
        "settings": "सेटिंग्स",
        "gen_btn": "क्विज़ बनाएं",
        "loading": "सिस्टम 1 प्रश्न ला रहा है... सिस्टम 2 जांच कर रहा है...",
        "submit": "क्विज़ जमा करें",
        "home": "होम"
    }
}

t = TRANS.get(st.session_state.language, TRANS["English"])

# --- SIDEBAR (Language & Nav) ---
with st.sidebar:
    st.title("⚙️ " + t["settings"])
    
    # Language Switcher
    lang_choice = st.radio("Language / भाषा", ["English", "Hindi"], 
                           index=0 if st.session_state.language == "English" else 1)
    
    if lang_choice != st.session_state.language:
        st.session_state.language = lang_choice
        st.rerun()

    st.markdown("---")
    if st.button("🏠 " + t["home"]):
        st.session_state.page = "home"
        st.session_state.quiz_data = None
        st.rerun()

# --- PAGE: HOME ---
if st.session_state.page == "home":
    st.title("🇮🇳 " + t["title"])
    st.markdown("### Prepare specifically for UPSC Prelims with AI-verified questions.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("Past Year Questions Analysis")
        if st.button(t["pyq_btn"], use_container_width=True):
            st.session_state.page = "pyq"
            st.rerun()
            
    with col2:
        st.info("Topic-wise Practice")
        if st.button(t["quiz_btn"], use_container_width=True):
            st.session_state.page = "quiz"
            st.rerun()

# --- PAGE: PYQ & QUIZ (Unified Logic) ---
elif st.session_state.page in ["pyq", "quiz"]:
    mode = st.session_state.page
    st.title(t["pyq_btn"] if mode == "pyq" else t["quiz_btn"])
    
    # -- Filters --
    with st.expander("Configuration", expanded=True):
        col_a, col_b, col_c = st.columns(3)
        
        subject = col_a.selectbox("Subject", ["History", "Geography", "Polity", "Economy", "Environment", "Science & Tech"])
        topic = col_b.text_input("Topic (Optional)", placeholder="e.g. Indus Valley")
        
        year = None
        subtopic = None
        
        if mode == "pyq":
            year = col_c.selectbox("Year", [str(y) for y in range(2023, 2010, -1)])
        else:
            subtopic = col_c.text_input("Sub-topic (Optional)")
            
        num_q = st.slider("Number of Questions", 5, 20, 5)
        
        if st.button(t["gen_btn"], type="primary"):
            with st.spinner(t["loading"]):
                # Call the Utils function
                data = utils.fetch_and_verify_questions(
                    mode=mode,
                    language=st.session_state.language,
                    count=num_q,
                    year=year,
                    subject=subject,
                    topic=topic,
                    subtopic=subtopic
                )
                st.session_state.quiz_data = data
                st.session_state.answers = {} # Reset answers
                st.rerun()

    # -- Display Quiz --
    if st.session_state.quiz_data:
        if isinstance(st.session_state.quiz_data, str):
            st.error(st.session_state.quiz_data) # Show error message if API failed
        else:
            st.markdown("---")
            for i, q in enumerate(st.session_state.quiz_data):
                st.subheader(f"Q{i+1}: {q['question']}")
                
                # Create unique key for radio to hold state
                choice = st.radio(
                    "Choose option:", 
                    q['options'], 
                    key=f"q_{i}", 
                    index=None
                )
                st.session_state.answers[i] = choice
                
                # Real-time Feedback (Optional, or wait for submit)
                # Showing toggle for explanation
                if st.toggle(f"Show Explanation Q{i+1}"):
                    if choice:
                        correct_opt = q['answer']
                        # Simple check: assumes answer is "A" or option text matches
                        st.info(f"Correct Answer: {q['answer']}")
                        st.caption(f"Explanation: {q['explanation']}")
                    else:
                        st.warning("Please select an option first.")
                st.markdown("---")
