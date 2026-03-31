from flask import Flask, request
import os
import json
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore


app = Flask(__name__)


# --- 1. SETUP GOOGLE GEMINI ---
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))


# --- 2. SETUP FIREBASE ---
# We load the JSON string from the environment variable we securely set in Render
firebase_key = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
if firebase_key:
    service_account_info = json.loads(firebase_key)
    cred = credentials.Certificate(service_account_info)
    firebase_admin.initialize_app(cred)
    db = firestore.client()


SYSTEM_PROMPT = """
You are GANI — proactive AI wellness agent for NEET aspirants.
Provide:
1. Risk Assessment
2. Study Plan
3. Wellness Tips
4. Proactive Advice
Use the user's recent history to give better, personalized advice.
"""


@app.route("/")
def home():
    return "GANI AI Agent with Memory Running"


@app.route('/ask', methods=['GET','POST'])
def ask():
    # Safely handle both GET and POST requests
    if request.method == 'POST':
        data = request.json or {}
    else:
        data = request.args


    prompt = data.get("prompt")
    # We use a default user_id for now. Later your Flutter app will send real IDs.
    user_id = data.get("user_id", "test_neet_student") 


    if not prompt:
        return {"error": "No prompt provided"}


    try:
        # --- 3. FETCH MEMORY FROM FIRESTORE ---
        user_ref = db.collection("users").document(user_id)
        doc = user_ref.get()
        
        history_text = ""
        if doc.exists:
            # Get the last 5 interactions to save space
            history = doc.to_dict().get("chat_history", [])
            history_text = "\n".join(history[-5:])


        # --- 4. CALL GEMINI WITH CONTEXT ---
        model = genai.GenerativeModel("gemini-1.5-flash")
        full_prompt = f"{SYSTEM_PROMPT}\n\nRecent History:\n{history_text}\n\nUser: {prompt}"
        
        response = model.generate_content(full_prompt)
        ai_reply = response.text


        # --- 5. SAVE NEW INTERACTION TO MEMORY ---
        new_interaction = f"User: {prompt}\nGANI: {ai_reply}"
        user_ref.set({
            "chat_history": firestore.ArrayUnion([new_interaction])
        }, merge=True)


        return {"response": ai_reply}


    except Exception as e:
        return {"error": str(e)}
