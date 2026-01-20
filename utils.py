import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import json
import time

# --- 2026 RESILIENT MODEL LIST ---
# These models are current leaders in free-tier stability and JSON accuracy
MODEL_FALLBACK_LIST = [
    "gemini-direct", # Direct Google API
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemini-2.0-flash-exp:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "mistralai/mistral-small-24b-instruct-2501:free"
]

def call_llm_provider(prompt, model_id):
    """Routes the request to either Gemini Direct or OpenRouter"""
    try:
        if model_id == "gemini-direct":
            if "GEMINI_API_KEY" not in st.secrets: return "ERR_KEY_MISSING"
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-1.5-flash')
            return model.generate_content(prompt).text
        else:
            if "OPENROUTER_API_KEY" not in st.secrets: return "ERR_KEY_MISSING"
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=st.secrets["OPENROUTER_API_KEY"],
            )
            completion = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": prompt}],
                response_format={ "type": "json_object" } # Requesting structured output
            )
            return completion.choices[0].message.content
    except Exception as e:
        return f"API_ERROR: {str(e)}"

# New version (fixes error)
def fetch_and_verify_questions(mode, language, count, subject, topic, **kwargs):
    
    # We can now use the extra data from kwargs
    year = kwargs.get('year', '')
    subtopic = kwargs.get('subtopic', '')
    
    # Update the prompt to include these details for better questions
    details = f"Subject: {subject}, Topic: {topic}"
    if year: details += f", Year: {year}"
    if subtopic: details += f", Subtopic: {subtopic}"

    prompt = f"""
    Act as a UPSC Prelims Examiner. 
    Generate {count} MCQs for {mode.upper()} mode.
    Details: {details}
    Language: {language}
    
    Output: Return ONLY a JSON array of objects. 
    Keys: "id", "question", "options" (list of 4), "answer" (Letter A, B, C, or D), "explanation".
    """
    
    # ... rest of your existing function code ...
    final_data = None
    
    # --- AUTOMATIC FAILOVER LOOP ---
    for model in MODEL_FALLBACK_LIST:
        with st.status(f"📡 Fetching questions (Source: {model.split('/')[-1]})..."):
            raw_response = call_llm_provider(prompt, model)
            
            if raw_response and "API_ERROR" not in raw_response:
                parsed = clean_and_parse(raw_response)
                if parsed: # If JSON is valid
                    final_data = parsed
                    break
            
            st.toast(f"Model {model} busy. Trying backup...", icon="🔄")
            time.sleep(1) 

    if not final_data:
        return "CRITICAL: All AI services are currently occupied. Please try again in 30 seconds."

    return final_data

def clean_and_parse(text):
    """Strips Markdown and parses text into Python list"""
    try:
        # Remove markdown code blocks if present
        if "```" in text:
            text = text.split("```json")[-1].split("```")[0].strip()
        return json.loads(text)
    except:
        return None
