from flask import Flask, request
import os
import google.generativeai as genai

app = Flask(__name__)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

SYSTEM_PROMPT = """
You are GANI — proactive AI wellness agent for NEET aspirants.
Provide:
1. Risk Assessment
2. Study Plan
3. Wellness Tips
4. Proactive Advice
"""

@app.route("/")
def home():
    return "GANI AI Agent Running"

@app.route('/ask', methods=['GET','POST'])
def ask():
prompt = request.args.get("prompt") or (request.json and request.json.get("prompt"))
model = genai.GenerativeModel("gemini-1.5-flash")
response = model.generate_content(SYSTEM_PROMPT + prompt)
    return {"response": response.text}

app.run(host="0.0.0.0", port=8080)
