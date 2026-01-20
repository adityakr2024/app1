import os
import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import json

# --- API CLIENT SETUP ---
def get_gemini_response(prompt):
    """System 1 & 2 Implementation using Gemini"""
    try:
        # Check if key exists
        if "GEMINI_API_KEY" not in st.secrets:
            return "Error: GEMINI_API_KEY not found in secrets."

        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"GEMINI ERROR: {str(e)}"

def get_openrouter_response(prompt):
    """Fail-safe Implementation using OpenRouter"""
    try:
        # Check if key exists
        if "OPENROUTER_API_KEY" not in st.secrets:
            return "Error: OPENROUTER_API_KEY not found in secrets."

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=st.secrets["OPENROUTER_API_KEY"],
        )
        # Trying a broader model list for stability
        completion = client.chat.completions.create(
            model="meta-llama/llama-3-8b-instruct:free",
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"OPENROUTER ERROR: {str(e)}"

# --- CORE LOGIC: THE TWO SYSTEMS ---

def fetch_and_verify_questions(mode, language, count, **kwargs):
    
    # Construct details based on mode
    if mode == "pyq":
        details = f"Year: {kwargs.get('year')}, Subject: {kwargs.get('subject')}, Topic: {kwargs.get('topic', 'Any')}"
    else: # Quiz mode
        details = f"Subject: {kwargs.get('subject')}, Topic: {kwargs.get('topic')}, Subtopic: {kwargs.get('subtopic', 'Any')}"

    # --- SYSTEM 1: GENERATOR ---
    sys1_prompt = f"""
    Act as a UPSC Prelims Question Database. 
    Task: Fetch/Generate {count} distinct multiple-choice questions (MCQs).
    Mode: {mode.upper()}
    Details: {details}
    Language: {language}
    
    Output Format: JSON only. Array of objects with keys: 'id', 'question', 'options' (list of A,B,C,D), 'answer' (correct option letter), 'explanation'.
    Ensure questions are strictly relevant to UPSC standards.
    """
    
    st.write("🔄 Attempting System 1 (Generator)...") # Debug UI Log
    raw_data = get_gemini_response(sys1_prompt)
    
    # Check if Gemini failed (if result starts with error or is None)
    if not raw_data or "ERROR" in raw_data:
        st.warning(f"System 1 Gemini Failed: {raw_data}") # Show error to user
        st.write("⚠️ Switching to OpenRouter Fallback...")
        raw_data = get_openrouter_response(sys1_prompt)
        
    if not raw_data or "ERROR" in raw_data:
        return f"CRITICAL FAILURE: Both APIs failed.\nGemini: {raw_data}\nOpenRouter: {raw_data}"

    # --- SYSTEM 2: VERIFIER ---
    sys2_prompt = f"""
    Act as a Senior UPSC Content Reviewer. 
    Task: Review the following JSON data of quiz questions.
    1. Check for factual accuracy.
    2. Ensure the language is strictly {language}.
    3. Verify the correct answer matches the explanation.
    4. Remove any markdown formatting (like ```json).
    
    Input JSON:
    {raw_data}
    
    Output Format: Return ONLY the cleaned, verified JSON string. No extra text.
    """
    
    st.write("✅ System 1 Done. 🔄 Attempting System 2 (Verifier)...") # Debug UI Log
    verified_data = get_gemini_response(sys2_prompt)
    
    if not verified_data or "ERROR" in verified_data:
        st.warning(f"System 2 Gemini Failed: {verified_data}")
        verified_data = get_openrouter_response(sys2_prompt)
        
    if not verified_data or "ERROR" in verified_data:
         # If verifier fails, try to return raw data as last resort
        return clean_json(raw_data) 

    return clean_json(verified_data)

def clean_json(text):
    """Helper to strip markdown and parse JSON"""
    try:
        # Clean potential error messages if they leaked into text
        if "ERROR" in text:
            return [{"question": "API Error", "options": ["Error"], "answer": "A", "explanation": text}]
            
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        st.error(f"JSON Parsing Error: {e}")
        st.text("Raw Output that failed to parse:")
        st.code(text)
        return []
