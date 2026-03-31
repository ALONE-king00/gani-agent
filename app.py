from flask import Flask, request
import os
import json
from google import genai
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# --- 1. SETUP GOOGLE GEMINI (NEW SDK) ---
gemini_key = os.environ.get("GEMINI_API_KEY", "")
try:
    ai_client = genai.Client(api_key=gemini_key)
    ai_error = "No error"
except Exception as e:
    ai_client = None
    ai_error = str(e)

# --- 2. FOOLPROOF FIREBASE SETUP ---
db = None
firebase_error = "No error"

try:
    firebase_key = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if not firebase_key:
        firebase_error = "The FIREBASE_SERVICE_ACCOUNT key is missing in Render."
    else:
        service_account_info = json.loads(firebase_key)
        if not firebase_admin._apps: 
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
        db = firestore.client()
except Exception as e:
    firebase_error = f"Firebase key error: {str(e)}"

SYSTEM_PROMPT = """
You are GANI — proactive AI wellness agent for NEET aspirants.
Provide:
1. Risk Assessment
2. Study Plan
3. Wellness Tips
4. Proactive Advice
Use the user's recent history to give better, personalized advice.
"""

# --- 3. HEALTH CHECK PAGE ---
@app.route("/")
def home():
    if db is None:
        return f"<h1>⚠️ GANI is awake, BUT the Database failed!</h1><p><b>Exact Error:</b> {firebase_error}</p>"
    if ai_client is None:
        return f"<h1>⚠️ Database works, BUT AI failed to connect!</h1><p><b>Exact Error:</b> {ai_error}</p>"
    return "<h1>✅ GANI AI Agent with Memory is Running Perfectly! 🚀</h1>"

# --- 4. GANI'S BRAIN ---
@app.route('/ask', methods=['GET','POST'])
def ask():
    if db is None:
        return {"error": "Database not connected", "details": firebase_error}
    if ai_client is None:
        return {"error": "AI not connected", "details": ai_error}

    data = request.json if request.is_json else request.args
    prompt = data.get("prompt")
    user_id = data.get("user_id", "test_neet_student") 

    if not prompt:
        return {"error": "No prompt provided"}

    try:
        # Fetch memory
        user_ref = db.collection("users").document(user_id)
        doc = user_ref.get()
        
        history_text = ""
        if doc.exists:
            history = doc.to_dict().get("chat_history", [])
            history_text = "\n".join(history[-5:])

        # Call AI (Using NEW SDK format and Upgraded Model)
        full_prompt = f"{SYSTEM_PROMPT}\n\nRecent History:\n{history_text}\n\nUser: {prompt}"
        
        response = ai_client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=full_prompt
        )
        ai_reply = response.text

        # Save to memory
        new_interaction = f"User: {prompt}\nGANI: {ai_reply}"
        user_ref.set({
            "chat_history": firestore.ArrayUnion([new_interaction])
        }, merge=True)

        return {"response": ai_reply}

    except Exception as e:
        return {"error": f"Something went wrong during AI generation: {str(e)}"}
