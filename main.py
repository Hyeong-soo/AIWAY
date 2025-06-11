from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import openai
import requests
import json
import os
import logging
import mimetypes
import tempfile

from dotenv import load_dotenv
load_dotenv()

# 환경변수
MCP_URL = os.getenv("MCP_SERVER_URL")
API_KEY = os.getenv("OPENAI_API_KEY")

# 로깅
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

missing = []
if not MCP_URL:
    missing.append("MCP_SERVER_URL")
if not API_KEY:
    missing.append("OPENAI_API_KEY")
if missing:
    raise EnvironmentError(
        f"Missing required environment variables: {', '.join(missing)}"
    )

# OpenAI 클라이언트 초기화
openai_client = openai.OpenAI(api_key=API_KEY)

# FastAPI 앱 초기화
app = FastAPI()

# CORS 허용 (모든 도메인 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 및 index.html 라우팅
app.mount("/static", StaticFiles(directory="public", html=True), name="static")

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "public", "index.html"))

@app.post("/ask")
async def ask(request: Request):
    try:
        body = await request.json()
        messages = body.get("messages", [])
        logger.info(f"Received messages: {messages}")

        if not messages:
            return JSONResponse(status_code=400, content={"error": "메시지가 제공되지 않았습니다."})

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
        else:
            messages += [first_response.choices[0].message]

        def stream_gpt():
            try:
                second_response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    stream=True
                )
                for chunk in second_response:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        yield delta.content
            except Exception as e:
                error_msg = f"[스트리밍 중 오류: {str(e)}]"
                logger.error(error_msg)
                yield error_msg

        return StreamingResponse(stream_gpt(), media_type="text/plain")

    except Exception as e:
        logger.exception("/ask 처리 중 예외 발생")
        return JSONResponse(status_code=500, content={"error": f"서버 오류: {str(e)}"})

@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    try:
        logger.info(f"Received audio file: {audio.filename}")

        suffix = mimetypes.guess_extension(audio.content_type or '') or ".webm"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            contents = await audio.read()
            temp.write(contents)
            temp.flush()
            temp_path = temp.name

        try:
            with open(temp_path, "rb") as f:
                transcript = openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    response_format="json"
                )
        finally:
            os.remove(temp_path)  # 파일 삭제

        logger.info(f"Transcript: {transcript.text}")
        return {"text": transcript.text or ""}

    except Exception as e:
        logger.exception("/transcribe 처리 중 예외 발생")
        return JSONResponse(status_code=500, content={"error": f"STT 처리 중 오류: {str(e)}"})
