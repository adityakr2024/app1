import streamlit as st
import utils # Ensure utils.py is in the same GitHub folder
import time

# --- 1. SETUP & CONFIG ---
st.set_page_config(page_title="UPSC Prep AI", page_icon="🏛️", layout="wide")

# Initialize Session States
if "page" not in st.session_state:
    st.session_state.page = "home"
if "language" not in st.session_state:
    st.session_state.language = "English"
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None

# --- 2. LANGUAGE TRANSLATIONS ---
TRANS = {
    "English": {
        "title": "UPSC Aspirant AI",
        "home_tag": "Master UPSC Prelims with AI-Verified Practice",
        "btn_pyq": "Previous Year Questions (PYQ)",
        "btn_quiz": "Take a Custom Quiz",
        "settings": "Settings",
        "lang_label": "Choose Language",
        "generate": "Generate Questions",
        "back": "Back to Home",
        "sub": "Subject",
        "top": "Topic",
        "stop": "Sub-topic",
        "year": "Exam Year",
        "q_count": "Number of Questions",
        "wait": "AI is fetching and verifying questions..."
    },
    "Hindi": {
        "title": "UPSC एस्पिरेंट AI",
        "home_tag": "AI-सत्यापित अभ्यास के साथ UPSC प्रीलिम्स में महारत हासिल करें",
        "btn_pyq": "पिछले वर्ष के प्रश्न (PYQ)",
        "btn_quiz": "कस्टम क्विज़ लें",
        "settings": "सेटिंग्स",
        "lang_label": "भाषा चुनें",
        "generate": "प्रश्न तैयार करें",
        "back": "होम पर वापस जाएं",
        "sub": "विषय",
        "top": "विषय (Topic)",
        "stop": "उप-विषय (Sub-topic)",
        "year": "परीक्षा का वर्ष",
        "q_count": "प्रश्नों की संख्या",
        "wait": "AI प्रश्न खोज और सत्यापित कर रहा है..."
    }
}

# Current translation dictionary
t = TRANS[st.session_state.language]

# --- 3. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.header(f"⚙️ {t['settings']}")
    
    # Language Toggle (Available at any time)
    new_lang = st.radio(t['lang_label'], ["English", "Hindi"], 
                        index=0 if st.session_state.language == "English" else 1)
    
    if new_lang != st.session_state.language:
        st.session_state.language = new_lang
        st.rerun()

    st.divider()
    if st.button(f"🏠 {t['back']}", use_container_width=True):
        st.session_state.page = "home"
        st.session_state.quiz_data = None
        st.rerun()

# --- 4. PAGE: HOME ---
if st.session_state.page == "home":
    st.title(f"🏛️ {t['title']}")
    st.subheader(t['home_tag'])
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("📊 **PYQ Section**\n\nFilter by year and subject to practice actual UPSC questions.")
        if st.button(t['btn_pyq'], type="primary", use_container_width=True):
            st.session_state.page = "pyq"
            st.rerun()
            
    with col2:
        st.success("🎯 **Quiz Section**\n\nGenerate dynamic questions for specific topics and subtopics.")
        if st.button(t['btn_quiz'], type="primary", use_container_width=True):
            st.session_state.page = "quiz"
            st.rerun()

# --- 5. PAGE: PYQ / QUIZ GENERATION ---
elif st.session_state.page in ["pyq", "quiz"]:
    mode = st.session_state.page
    st.title(t['btn_pyq'] if mode == "pyq" else t['btn_quiz'])
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            subject = st.selectbox(t['sub'], ["History", "Geography", "Polity", "Economy", "Environment", "Science", "Current Affairs"])
            topic = st.text_input(t['top'] + " (Optional)", placeholder="e.g., Buddhism, Preamble")
        
        with c2:
            if mode == "pyq":
                year = st.selectbox(t['year'], [str(y) for y in range(2024, 2010, -1)])
                subtopic = ""
            else:
                subtopic = st.text_input(t['stop'] + " (Optional)")
                year = ""
            
            num_q = st.slider(t['q_count'], 5, 20, 5)

        if st.button(t['generate'], use_container_width=True):
            with st.spinner(t['wait']):
                # Calls the 2-system logic in utils.py
                result = utils.fetch_and_verify_questions(
                    mode=mode,
                    language=st.session_state.language,
                    count=num_q,
                    subject=subject,
                    topic=topic,
                    subtopic=subtopic,
                    year=year
                )
                st.session_state.quiz_data = result
                st.session_state.current_q = 0

    # --- 6. DISPLAYING THE QUIZ ---
    if st.session_state.quiz_data:
        st.divider()
        questions = st.session_state.quiz_data
        
        if isinstance(questions, str):
            st.error(questions) # Error from API
        else:
            for i, q in enumerate(questions):
                st.markdown(f"### Q{i+1}. {q['question']}")
                # Unique key prevents widget overlap
                ans = st.radio("Options:", q['options'], key=f"q_{mode}_{i}")
                
                with st.expander("Check Answer & Explanation"):
                    # Basic verification: Checking if the selected text matches index of correct answer
                    correct_idx = ord(q['answer']) - ord('A') # A=0, B=1...
                    if ans == q['options'][correct_idx]:
                        st.success(f"Correct! (Answer: {q['answer']})")
                    else:
                        st.error(f"Incorrect. Correct Answer: {q['answer']}")
                    st.write(f"**Explanation:** {q['explanation']}")
                st.divider()
