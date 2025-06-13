"""
FastAPI server providing STT, chat completion and TTS endpoints.

Endpoints:
- `/` serves the demo page.
- `/transcribe` converts uploaded audio to text.
- `/speak` engages GPT, uses MCP tools if needed, and returns text with speech.
- `/log` records client log messages.
"""

from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import openai
import os
import logging
import mimetypes
import tempfile
import subprocess
import requests
import base64
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()
MCP_URL = os.getenv("MCP_SERVER_URL")
API_KEY = os.getenv("OPENAI_API_KEY")

# 필수 체크
missing = []
if not MCP_URL:
    missing.append("MCP_SERVER_URL")
if not API_KEY:
    missing.append("OPENAI_API_KEY")
if missing:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI 클라이언트 초기화
openai_client = openai.OpenAI(api_key=API_KEY)

# FastAPI 앱 초기화
app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙
app.mount("/static", StaticFiles(directory="public", html=True), name="static")

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "public", "index.html"))

@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    try:
        logger.info(f"Received audio file: {audio.filename}")
        suffix = mimetypes.guess_extension(audio.content_type or '') or ".webm"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            contents = await audio.read()
            if not contents:
                raise ValueError("오디오 파일이 비어있습니다.")
            temp.write(contents)
            temp.flush()
            temp_path = temp.name

        def get_audio_info(path):
            try:
                result = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=format_name",
                     "-of", "default=noprint_wrappers=1:nokey=1", path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=5
                )
                return result.stdout.strip()
            except Exception as e:
                return f"ffprobe error: {str(e)}"

        detected_format = get_audio_info(temp_path)
        logger.info(f"Detected audio format: {detected_format}")

        try:
            with open(temp_path, "rb") as f:
                transcript = openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    response_format="json",
                    language="ko"
                )
        finally:
            os.remove(temp_path)

        logger.info(f"Transcript: {transcript.text}")
        return {"text": transcript.text or ""}

    except Exception as e:
        logger.exception("STT 처리 중 오류")
        return JSONResponse(status_code=500, content={"error": f"STT 오류: {str(e)}"})


@app.post("/speak")
async def speak(request: Request):
    try:
        body = await request.json()
        messages = body.get("messages", [])
        voice = body.get("voice", "nova")

        if not messages:
            return JSONResponse(status_code=400, content={"error": "messages 필드가 필요합니다."})

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "description": "현재 시간을 반환합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]

        first_response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            stream=False
        )

        tool_calls = first_response.choices[0].message.tool_calls
        logger.info(f"Tool calls: {tool_calls}")

        if tool_calls:
            call = tool_calls[0]
            tool_call_id = call.id
            tool_name = call.function.name

            mcp_payload = {
                "jsonrpc": "2.0",
                "method": tool_name,
                "id": "1"
            }

            try:
                logger.info(f"Calling MCP: {tool_name}")
                mcp_resp = requests.post(MCP_URL, json=mcp_payload, timeout=5)
                mcp_resp.raise_for_status()
                tool_result = mcp_resp.json().get("result", "결과 없음")
                logger.info(f"MCP result: {tool_result}")
            except Exception as e:
                tool_result = f"MCP 호출 오류: {str(e)}"
                logger.error(tool_result)

            messages += [
                first_response.choices[0].message,
                {
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "name": tool_name,
                    "content": str(tool_result)
                }
            ]

            final_response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            gpt_text = final_response.choices[0].message.content.strip()
        else:
            gpt_text = first_response.choices[0].message.content.strip()

        if not gpt_text:
            return JSONResponse(content={"text": "", "audio": ""})

        audio_response = openai_client.audio.speech.create(
            model="gpt-4o-mini-tts",
            input=gpt_text,
            voice=voice,
            response_format="mp3"
        )

        audio_bytes = b"".join(audio_response.iter_bytes())
        encoded_audio = base64.b64encode(audio_bytes).decode("utf-8")

        return JSONResponse(content={
            "text": gpt_text,
            "audio": encoded_audio
        })

    except Exception as e:
        logger.exception("/speak 처리 중 예외")
        return JSONResponse(status_code=500, content={"error": f"TTS 오류: {str(e)}"})


@app.post("/log")
async def log_message(request: Request):
    try:
        data = await request.json()
        msg = data.get("message", "")
        logger.info(f"[CLIENT LOG] {msg}")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"로그 수신 중 오류: {str(e)}")
        return JSONResponse(status_code=400, content={"error": str(e)})
