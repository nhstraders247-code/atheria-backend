import os
import io
import tempfile
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
import google.generativeai as genai
from gtts import gTTS
from pydub import AudioSegment

app = FastAPI()

# Configure Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Custom System Prompt for Atheria
CREATOR_NAME = "Ratul"         # Replace with your name
SCHOOL_NAME = "Thakurnagar High School"   # Replace with your school name

SYSTEM_INSTRUCTION = f"""
Your name is Atheria. You are an AI voice assistant created by {CREATOR_NAME} for {SCHOOL_NAME}.
You are friendly, helpful, and concise.
You can converse fluently in Bengali, Hindi, and English.
Always answer in the same language the user speaks to you.
Keep responses short (1-2 sentences maximum) so they can be converted to speech quickly.
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

@app.get("/")
def health_check():
    return {"status": "Atheria backend is live!"}

@app.post("/process-voice")
async def process_voice(request: Request):
    try:
        audio_bytes = await request.body()

        if len(audio_bytes) < 1000:
            user_prompt = "Hello! Please introduce yourself briefly."
            response = model.generate_content(user_prompt)
        else:
            audio_part = {
                "mime_type": "audio/wav",
                "data": audio_bytes
            }
            response = model.generate_content([audio_part, "Listen to this audio and reply concisely as Atheria."])

        bot_reply = response.text if response.text else "Hello, I am Atheria!"
        print(f"Atheria reply: {bot_reply}")

        # Convert reply to speech
        tts = gTTS(text=bot_reply, lang='en', slow=False)
        
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)

        # Convert MP3 to 16kHz, 1-channel (mono), 16-bit PCM
        audio_segment = AudioSegment.from_file(mp3_fp, format="mp3")
        audio_segment = audio_segment.set_frame_rate(16000).set_channels(1).set_sample_width(2)

        # Return RAW PCM bytes directly (No WAV header)
        return Response(content=audio_segment.raw_data, media_type="application/octet-stream")

    except Exception as e:
        print(f"Error in backend: {e}")
        return Response(content=b"", status_code=500)
