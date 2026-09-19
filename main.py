import os
from fastapi import FastAPI, Form, Response
from google import genai
from google.genai import types
from twilio.twiml.voice_response import VoiceResponse, Gather

app = FastAPI()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

@app.post("/voice")
def handle_incoming_call():
    response = VoiceResponse()
    gather = Gather(input="speech", action="/process-speech", method="POST", timeout=3)
    gather.say("Hello! What question would you like me to look up on Google?")
    response.append(gather)
    response.say("I didn't hear anything. Goodbye!")
    return Response(content=str(response), media_type="application/xml")

@app.post("/process-speech")
def process_speech(SpeechResult: str = Form(...)):
    response = VoiceResponse()
    try:
        gemini_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Answer in 2 short sentences suitable for a phone call: {SpeechResult}",
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )
        answer = gemini_response.text
    except Exception:
        answer = "Sorry, I ran into an error searching for an answer."

    response.say(answer)
    gather = Gather(input="speech", action="/process-speech", method="POST", timeout=3)
    gather.say("Do you have another question?")
    response.append(gather)
    return Response(content=str(response), media_type="application/xml")