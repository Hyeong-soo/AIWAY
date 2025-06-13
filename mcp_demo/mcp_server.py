"""
Minimal MCP server exposing tools via a JSON-RPC interface.

Tools are registered in `TOOL_REGISTRY` mapping method names to callables.
The `/mcp` endpoint dispatches incoming requests to the appropriate tool.
"""

from fastapi import FastAPI, Request
from .tools import time_tool
from .mcp_schema import MCPRequest, MCPResponse

app = FastAPI()

# 사용할 MCP 도구들을 등록해놓은 딕셔너리
# method 이름을 키로, 실행할 함수를 값으로 매핑
TOOL_REGISTRY = {
    "get_current_time": time_tool.get_current_time,
}

# MCP 요청을 처리하는 엔드포인트 정의
@app.post("/mcp")
async def handle_mcp(req: Request):
    # JSON 형식으로 들어온 요청 데이터를 파싱
    data = await req.json()

    # Pydantic 모델을 사용해 유효성 검사 및 파싱
    mcp_request = MCPRequest(**data)

    # 요청된 method가 TOOL_REGISTRY에 없으면 에러 반환
    if mcp_request.method not in TOOL_REGISTRY:
        return MCPResponse(
            id=mcp_request.id,
            error={"code": -32601, "message": "Method not found"}  # JSON-RPC 표준 에러 코드
        )

    try:
        # method 이름에 해당하는 도구 함수 호출
        # params가 None일 수 있으므로 기본값 {} 사용
        result = TOOL_REGISTRY[mcp_request.method](mcp_request.params or {})

        # 성공 응답 생성
        return MCPResponse(id=mcp_request.id, result=result)
    except Exception as e:
        # 예외 발생 시 에러 응답 반환
        return MCPResponse(id=mcp_request.id, error={"code": -32000, "message": str(e)})
