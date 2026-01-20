import streamlit as st
import utils

# --- PAGE CONFIG ---
st.set_page_config(page_title="UPSC AI Quiz Master", page_icon="🏛️", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .question-box { background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "quiz_data" not in st.session_state: st.session_state.quiz_data = None
if "current_q" not in st.session_state: st.session_state.current_q = 0
if "score" not in st.session_state: st.session_state.score = 0

# --- SIDEBAR ---
with st.sidebar:
    st.image("[https://upload.wikimedia.org/wikipedia/commons/e/e4/Seal_of_the_UPSC.png](https://upload.wikimedia.org/wikipedia/commons/e/e4/Seal_of_the_UPSC.png)", width=100)
    st.title("UPSC Prelims 2026")
    st.divider()
    
    mode = st.radio("Quiz Mode", ["Practice", "Previous Year (PYQ)"])
    lang = st.selectbox("Language", ["English", "Hindi"])
    q_count = st.slider("Number of Questions", 5, 20, 10)
    
    if st.button("🔄 Reset Quiz"):
        st.session_state.quiz_data = None
        st.session_state.current_q = 0
        st.session_state.score = 0
        st.rerun()

# --- MAIN UI ---
st.header("🏛️ UPSC AI Question Generator")

if st.session_state.quiz_data is None:
    # INPUT SECTION
    col1, col2 = st.columns(2)
    with col1:
        subject = st.text_input("Subject", placeholder="e.g., Indian Polity, Economy")
    with col2:
        topic = st.text_input("Topic", placeholder="e.g., Fundamental Rights, Inflation")
    
    if st.button("✨ Generate My Quiz"):
        if subject and topic:
            result = utils.fetch_and_verify_questions(mode, lang, q_count, subject, topic)
            if isinstance(result, str): # Error message
                st.error(result)
            else:
                st.session_state.quiz_data = result
                st.rerun()
        else:
            st.warning("Please enter both Subject and Topic to continue.")

else:
    # QUIZ SECTION
    data = st.session_state.quiz_data
    curr = st.session_state.current_q
    
    if curr < len(data):
        q = data[curr]
        st.progress((curr) / len(data))
        st.subheader(f"Question {curr + 1} of {len(data)}")
        
        with st.container():
            st.markdown(f"**{q['question']}**")
            
            # Show options as buttons or radio
            choice = st.radio("Select your answer:", q['options'], key=f"q_{curr}")
            
            if st.button("Submit Answer"):
                correct_ans = q['answer'] # A, B, C, or D
                # Find the text of the correct option
                idx = ord(correct_ans) - ord('A')
                
                if choice == q['options'][idx]:
                    st.success("🎯 Correct!")
                    st.session_state.score += 1
                else:
                    st.error(f"❌ Incorrect. The correct answer was ({correct_ans})")
                
                with st.expander("See Explanation"):
                    st.write(q['explanation'])
                
                if st.button("Next Question ➡️"):
                    st.session_state.current_q += 1
                    st.rerun()
    else:
        # RESULTS SECTION
        st.balloons()
        st.success(f"### Quiz Completed! 🎉")
        st.metric("Final Score", f"{st.session_state.score} / {len(data)}")
        if st.button("Try Another Quiz"):
            st.session_state.quiz_data = None
            st.rerun()
