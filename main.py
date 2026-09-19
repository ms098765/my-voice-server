import os
import time
import json
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from google import genai
from google.genai import types

app = FastAPI()

@app.post("/chat/completions")
async def custom_llm(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = {}
        
    # 1. Get the user's voice question from Vapi
    messages = data.get("messages", [])
    user_prompt = "Hello"
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_prompt = msg.get("content", "")
            break

    # 2. Safely query Google Gemini
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            answer = "Server error. The Gemini API key is missing from Render."
        else:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"Answer concisely in 2 short sentences for a phone call: {user_prompt}",
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                ),
            )
            answer = response.text
    except Exception as e:
        answer = "Sorry, I encountered an internal error while searching Google."

    # 3. Format the response exactly how Vapi expects it (Streaming Data)
    is_stream = data.get("stream", False)
    
    if is_stream:
        async def event_generator():
            chunk = {
                "id": "chatcmpl-1",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": "gemini-2.5-flash",
                "choices": [{"index": 0, "delta": {"content": answer}, "finish_reason": None}]
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            
            stop_chunk = {
                "id": "chatcmpl-1",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": "gemini-2.5-flash",
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
            }
            yield f"data: {json.dumps(stop_chunk)}\n\n"
            yield "data: [DONE]\n\n"
            
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    else:
        return {
            "id": "chatcmpl-1",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "gemini-2.5-flash",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": answer}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }
