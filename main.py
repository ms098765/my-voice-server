import os
from fastapi import FastAPI, Request
from google import genai
from google.genai import types

app = FastAPI()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

@app.post("/chat/completions")
async def custom_llm(request: Request):
    data = await request.json()
    
    # Extract messages from Vapi
    messages = data.get("messages", [])
    
    # Get the caller's last message
    user_prompt = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_prompt = msg.get("content", "")
            break
            
    if not user_prompt:
        user_prompt = "Hello"

    try:
        # Query Gemini with Google Search enabled
        gemini_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Answer concisely in 2 short sentences for a phone call: {user_prompt}",
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )
        answer = gemini_response.text
    except Exception:
        answer = "Sorry, I had trouble searching for an answer."

    # Return standard OpenAI format expected by Vapi
    return {
        "id": "chatcmpl-vapi-gemini",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": answer
                },
                "finish_reason": "stop"
            }
        ]
    }
