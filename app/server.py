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

    async def send_json(payload: dict):
        await websocket.send_text(json.dumps(payload))

    try:
        async with client.aio.live.connect(model=MODEL, config=LIVE_CONFIG) as session:

            async def browser_to_gemini():
                while True:
                    message = await websocket.receive()
                    if message.get("type") == "websocket.disconnect":
                        return
                    audio = message.get("bytes")
                    if audio:
                        await session.send_realtime_input(
                            audio=types.Blob(data=audio, mime_type="audio/pcm;rate=16000")
                        )
                        continue
                    text = message.get("text")
                    if not text:
                        continue
                    try:
                        user_text = (json.loads(text).get("text") or "").strip()
                    except json.JSONDecodeError:
                        await send_json({"type": "error", "message": "Invalid JSON format"})
                        continue
                    if user_text:
                        log.info("User: %s", user_text)
                        await session.send_realtime_input(text=user_text)

            async def gemini_to_browser():
                user_tx, model_tx = "", ""
                while True:
                    async for response in session.receive():
                        if response.tool_call:
                            replies = []
                            for call in response.tool_call.function_calls:
                                event, result = await asyncio.to_thread(
                                    dispatch_tool, call.name, dict(call.args or {})
                                )
                                await send_json({"type": "tool", "event": event})
                                replies.append(
                                    types.FunctionResponse(id=call.id, name=call.name, response=result)
                                )
                            await session.send_tool_response(function_responses=replies)
                            continue

                        content = response.server_content
                        if not content:
                            continue
                        if content.input_transcription and content.input_transcription.text:
                            user_tx += content.input_transcription.text
                        if content.output_transcription and content.output_transcription.text:
                            model_tx += content.output_transcription.text
                        if content.model_turn:
                            for part in content.model_turn.parts or []:
                                if part.inline_data and part.inline_data.data:
                                    await websocket.send_bytes(part.inline_data.data)
                        if content.interrupted:
                            await send_json({"type": "interrupted"})
                        if content.turn_complete:
                            if user_tx.strip():
                                await send_json({"type": "user", "text": user_tx.strip()})
                            if model_tx.strip():
                                await send_json({"type": "text", "text": model_tx.strip()})
                            user_tx, model_tx = "", ""
                            await send_json({"type": "turn_complete"})

            tasks = [
                asyncio.create_task(browser_to_gemini()),
                asyncio.create_task(gemini_to_browser()),
            ]
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            for task in done:
                task.result()
    except WebSocketDisconnect:
        log.info("Client disconnected")
    except Exception as e:
        log.exception("Gemini session error")
        try:
            await send_json({"type": "error", "message": f"Gemini error: {e}"})
        except Exception:
            pass


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
