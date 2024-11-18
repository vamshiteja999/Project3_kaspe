from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig, Part
from google.cloud import texttospeech
import os
import io
from pydub import AudioSegment
from datetime import datetime
from typing import Optional
import uvicorn
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import os
from pathlib import Path


# Use /tmp for temporary files
TEMP_DIR = Path("/tmp")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Audio Analysis API")

# Mount static files if they exist
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
# Update audio file path
LATEST_AUDIO_FILE = TEMP_DIR / "latest_response.mp3"
# Initialize vertexai
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "application_default_credentials.json"
vertexai.init(project="voicellapp", location="us-central1")




async def clean_audio_data(audio_data: bytes, original_format: str = None) -> Optional[io.BytesIO]:
    try:
        audio_buffer = io.BytesIO()
        if original_format == 'mp3':
            audio_buffer.write(audio_data)
        else:
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format=original_format or 'wav')
            audio = audio.set_channels(1).set_frame_rate(44100)
            audio.export(audio_buffer, format='mp3', parameters=["-q:a", "0"])
        audio_buffer.seek(0)
        return audio_buffer
    except Exception as e:
        print(f"Error cleaning audio: {str(e)}")
        return None

async def analyze_audio(audio_buffer: io.BytesIO) -> Optional[str]:
    model = GenerativeModel("gemini-1.5-pro")
    prompt = """
    Please analyze this audio and provide:
    1. Detailed transcription with:
    - Timestamps in [HH:MM:SS] format
    - Speaker identification (Speaker A, B, etc.)
    2. Sentiment analysis for:
    - Overall conversation tone
    - Each speaker's emotional state
    - Key emotional moments
    Format the response as:
    Transcription:
    [timestamp] Speaker: text
    Sentiment Analysis:
    Overall Tone:
    Speaker Analysis:
    Key Emotional Moments:
    """
    try:
        audio_content = audio_buffer.getvalue()
        mime_type = "audio/mpeg"
        audio_part = Part.from_data(data=audio_content, mime_type=mime_type)
        response = model.generate_content(
            contents=[audio_part, prompt],
            generation_config=GenerationConfig(
                temperature=0.2,
                top_k=40,
                top_p=0.95,
                audio_timestamp=True
            )
        )
        return response.text
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        return None

def clean_text_for_speech(text: str) -> str:
    parts = text.split('Sentiment Analysis:')
    transcription = parts[0].replace('Transcription:', '').strip()
    sentiment = parts[1].strip() if len(parts) > 1 else ''
    cleaned_sentiment = sentiment.replace('**', '').replace('##', '')
    cleaned_sentiment = cleaned_sentiment.replace('[', '').replace(']', '')
    cleaned_sentiment = ' '.join(line.strip() for line in cleaned_sentiment.split('\n') if line.strip())
    clean_text = f"Transcription: {transcription}\n\nSentiment Analysis: {cleaned_sentiment}"
    return clean_text.replace('*', '').replace('#', '')

async def text_to_speech(text: str) -> Optional[str]:
    try:
        clean_text = clean_text_for_speech(text)
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=clean_text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Neural2-F",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.9,
            pitch=0.0,
            effects_profile_id=["telephony-class-application"]
        )
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        with open(LATEST_AUDIO_FILE, "wb") as f:
            f.write(response.audio_content)
        return str(LATEST_AUDIO_FILE)
    except Exception as e:
        print(f"Error during text-to-speech conversion: {str(e)}")
        return None

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_audio(audio: UploadFile = File(...)):
    try:
        audio_data = await audio.read()
        audio_buffer = await clean_audio_data(audio_data, 'mp3')
        if not audio_buffer:
            raise HTTPException(status_code=500, detail="Failed to process audio")
        
        analysis = await analyze_audio(audio_buffer)
        if not analysis:
            raise HTTPException(status_code=500, detail="Analysis failed")
        
        audio_file_path = await text_to_speech(analysis)
        if not audio_file_path:
            raise HTTPException(status_code=500, detail="Text-to-speech failed")
        
        parts = analysis.split('Sentiment Analysis:')
        return JSONResponse({
            'success': True,
            'transcription': parts[0].strip(),
            'sentiment': parts[1].strip() if len(parts) > 1 else '',
            'audio_url': '/get_audio'
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_audio_endpoint(file: UploadFile = File(...)):
    try:
        audio_data = await file.read()
        file_ext = file.filename.split('.')[-1].lower()
        audio_buffer = await clean_audio_data(audio_data, file_ext)
        if not audio_buffer:
            raise HTTPException(status_code=500, detail="Failed to process audio")
        
        analysis = await analyze_audio(audio_buffer)
        if not analysis:
            raise HTTPException(status_code=500, detail="Analysis failed")
        
        audio_file_path = await text_to_speech(analysis)
        if not audio_file_path:
            raise HTTPException(status_code=500, detail="Text-to-speech failed")
        
        parts = analysis.split('Sentiment Analysis:')
        return JSONResponse({
            'success': True,
            'transcription': parts[0].strip(),
            'sentiment': parts[1].strip() if len(parts) > 1 else '',
            'audio_url': '/get_audio'
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_audio")
async def get_audio(request: Request):
    if LATEST_AUDIO_FILE.exists():
        return FileResponse(
            LATEST_AUDIO_FILE,
            media_type="audio/mpeg",
            filename="response.mp3",
            headers={
                "Accept-Ranges": "bytes"
            }
        )
    raise HTTPException(status_code=404, detail="No audio response available")

@app.get("/health")
async def health():
    return {"status": "OK"}

if __name__ == "__main__":
    # Clean up temp files on startup
    for file in TEMP_DIR.glob("*"):
        file.unlink()
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)