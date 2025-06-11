from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import openai, requests
import json, os

from dotenv import load_dotenv
load_dotenv()
MCP_URL = os.getenv("MCP_SERVER_URL")
API_KEY = os.getenv("OPENAI_API_KEY")

missing = []
if not MCP_URL:
    missing.append("MCP_SERVER_URL")
if not API_KEY:
    missing.append("OPENAI_API_KEY")
if missing:
    raise EnvironmentError(
        f"Missing required environment variables: {', '.join(missing)}"
    )

openai_client = openai.OpenAI(api_key=API_KEY)

app = FastAPI()

app.mount("/static", StaticFiles(directory="public", html=True), name="static")

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "public", "index.html"))

@app.post("/ask")
async def ask(request: Request):
    body = await request.json()
    question = body["question"]

    messages = [{"role": "user", "content": question}]
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

    # 1단계: GPT에게 tool_call 유도 (stream=False)
    first_response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto",
        stream=False
    )

    tool_calls = first_response.choices[0].message.tool_calls

    if tool_calls:
        # tool_call 발생 → MCP 호출 후 결과 삽입
        call = tool_calls[0]
        tool_call_id = call.id
        tool_name = call.function.name

        mcp_payload = {
            "jsonrpc": "2.0",
            "method": tool_name,
            "id": "1"
        }
        mcp_resp = requests.post(MCP_URL, json=mcp_payload)
        tool_result = mcp_resp.json()["result"]

        # 메시지 업데이트
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

    # 2단계: 최종 응답 스트리밍
    def stream_gpt():
        second_response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            stream=True
        )
        for chunk in second_response:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                yield delta.content

    return StreamingResponse(stream_gpt(), media_type="text/plain")
