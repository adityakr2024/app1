import os
import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import json

# --- API CLIENT SETUP ---
def get_gemini_response(prompt):
    """System 1 & 2 Implementation using Gemini Direct"""
    try:
        if "GEMINI_API_KEY" not in st.secrets:
            return "ERROR: GEMINI_API_KEY missing in Streamlit Secrets"
            
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"GEMINI_SYSTEM_ERROR: {str(e)}"

def get_openrouter_response(prompt):
    """Fail-safe Implementation using OpenRouter"""
    try:
        if "OPENROUTER_API_KEY" not in st.secrets:
            return "ERROR: OPENROUTER_API_KEY missing in Streamlit Secrets"

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=st.secrets["OPENROUTER_API_KEY"],
        )
        
        # Using a more reliable free model identifier
        completion = client.chat.completions.create(
            model="google/gemini-2.0-flash-exp:free", 
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"OPENROUTER_SYSTEM_ERROR: {str(e)}"

# --- CORE LOGIC: THE TWO SYSTEMS ---

def fetch_and_verify_questions(mode, language, count, **kwargs):
    # Construct details
    details = f"Subject: {kwargs.get('subject')}, Topic: {kwargs.get('topic', 'General')}"
    if mode == "pyq":
        details += f", Year: {kwargs.get('year')}"
    else:
        details += f", Subtopic: {kwargs.get('subtopic', 'General')}"

    sys1_prompt = f"""
    Act as a UPSC Prelims Question Expert. 
    Generate {count} MCQs for {mode.upper()}.
    Details: {details}.
    Language: {language}.
    Format: JSON array of objects with keys: id, question, options (list of 4), answer (A, B, C, or D), explanation.
    Strictly UPSC standard.
    """
    
    # --- TRY SYSTEM 1 ---
    st.write(f"🔄 System 1: Fetching {mode} questions...")
    raw_data = get_gemini_response(sys1_prompt)
    
    if "ERROR" in raw_data:
        st.warning("Gemini Primary failed. Trying OpenRouter Fallback...")
        raw_data = get_openrouter_response(sys1_prompt)
    
    if "ERROR" in raw_data:
        return f"Critical Failure: Both APIs failed to generate questions. Detail: {raw_data}"

    # --- TRY SYSTEM 2 ---
    st.write("✅ System 1 complete. 🔄 System 2: Verifying data...")
    sys2_prompt = f"Verify this UPSC JSON data for accuracy and {language} language. Return ONLY valid JSON: {raw_data}"
    
    verified_data = get_gemini_response(sys2_prompt)
    if "ERROR" in verified_data:
        verified_data = get_openrouter_response(sys2_prompt)
        
    # If verifier fails, try to use raw data anyway so the user gets something
    if "ERROR" in verified_data:
        st.warning("Verification failed, attempting to parse raw data...")
        return clean_json(raw_data)

    return clean_json(verified_data)

def clean_json(text):
    try:
        # Strip code blocks if present
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        st.error("JSON Structure Error")
        return []
