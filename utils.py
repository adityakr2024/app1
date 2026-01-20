import os
import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import json

# --- API CLIENT SETUP ---
def get_gemini_response(prompt):
    """System 1 & 2 Implementation using Gemini"""
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return None

def get_openrouter_response(prompt):
    """Fail-safe Implementation using OpenRouter"""
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=st.secrets["OPENROUTER_API_KEY"],
        )
        completion = client.chat.completions.create(
            model="meta-llama/llama-3-8b-instruct:free", # Using a free/cheap model as fallback
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"OpenRouter Error: {e}")
        return None

# --- CORE LOGIC: THE TWO SYSTEMS ---

def fetch_and_verify_questions(mode, language, count, **kwargs):
    """
    Orchestrates the 2-System Workflow:
    System 1: Fetch/Generate Raw Questions
    System 2: Verify & Crosscheck
    """
    
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
    
    raw_data = get_gemini_response(sys1_prompt)
    
    # Fail-safe: Switch to OpenRouter if Gemini fails
    if not raw_data:
        raw_data = get_openrouter_response(sys1_prompt)
        
    if not raw_data:
        return "Error: Both API services failed to respond."

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
    
    verified_data = get_gemini_response(sys2_prompt)
    
    # Fail-safe for Verifier
    if not verified_data:
        verified_data = get_openrouter_response(sys2_prompt)
        
    return clean_json(verified_data)

def clean_json(text):
    """Helper to strip markdown and parse JSON"""
    try:
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        st.error(f"Data parsing error: {e}")
        return []
