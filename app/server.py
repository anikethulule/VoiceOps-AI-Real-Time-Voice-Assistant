"""FastAPI + Gemini Live backend for VoiceOps AI Assistant."""

import asyncio
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from google import genai
from google.genai import types

from app.persona import VOICEOPS_INSTRUCTION
from app.tools import TOOL_DECLARATIONS, dispatch_tool

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
log = logging.getLogger("voiceops-ai")

MODEL = os.getenv("LIVE_MODEL", "gemini-3.8-live")
VOICE = os.getenv("LIVE_VOICE", "Aoede")

client = genai.Client()

LIVE_CONFIG = {
    "response_modalities": ["AUDIO"],
    "system_instruction": VOICEOPS_INSTRUCTION,
    "input_audio_transcription": {},
    "output_audio_transcription": {},
    "speech_config": {
        "voice_config": {
            "prebuilt_voice_config": {"voice_name": VOICE}
        }
    },
    "tools": [{"function_declarations": TOOL_DECLARATIONS}],
}

app = FastAPI(title="VoiceOps AI - Real-Time Voice Assistant", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "application": "VoiceOps AI - Real-Time Voice Assistant",
        "model": MODEL,
        "voice": VOICE,
    }


@app.websocket("/ws")
async def voice_socket(websocket: WebSocket):
    await websocket.accept()
    log.info("Browser connected")
    
    try:
        while True:
            message = await websocket.receive()
            text = message.get("text")
            if text:
                try:
                    if isinstance(text, str):
                        data = json.loads(text)
                    else:
                        data = text
                    user_text = data.get("text", "").strip()
                    if user_text:
                        log.info("User: %s", user_text)
                        # Send back a demo response
                        response_text = f"Echo: You said '{user_text}'. I'm in demo mode - Gemini API not configured."
                        await websocket.send_text(json.dumps({
                            "type": "text",
                            "text": response_text
                        }))
                except json.JSONDecodeError as e:
                    log.error("JSON Error: %s", e)
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }))
                except Exception as e:
                    log.error("Error: %s", e)
    except WebSocketDisconnect:
        log.info("Client disconnected")
    except Exception as e:
        log.error("WebSocket error: %s", e)


FRONTEND = ROOT / "frontend"


# Serve static files and handle SPA routing
@app.get("/{path_name:path}")
async def serve_static(path_name: str):
    # Try to serve the file directly
    if path_name:
        file_path = FRONTEND / path_name
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
    
    # Serve index.html for all non-file routes (SPA routing)
    index_path = FRONTEND / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    
    return {"error": "Not found"}, 404


@app.get("/")
async def serve_root():
    index_path = FRONTEND / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"error": "Not found"}, 404
