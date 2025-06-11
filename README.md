# MCP

이 프로젝트는 Model Context Protocol(MCP)을 이용해 현재 시간을 제공하는 간단한 도구와 이를 사용하는 예제 서버를 포함합니다.

## 구성

- `mcp_demo/mcp_server.py` : MCP 요청을 처리하는 FastAPI 서버입니다. `/mcp` 경로에서 JSON-RPC 형식으로 도구를 호출할 수 있습니다.
- `mcp_demo/tools/time_tool.py` : `get_current_time()` 함수를 정의하며, 서울 시간 기준 현재 시각을 반환합니다.
- `main.py` : OpenAI API와 MCP 서버를 연동하여 질문에 따라 도구를 호출하고, 결과를 스트리밍 방식으로 전달합니다.
- `public/index.html` : 웹 브라우저에서 시간을 질문해 볼 수 있는 간단한 페이지입니다.

## 환경 변수

`.env` 파일에 다음 값을 설정해야 합니다.

```env
OPENAI_API_KEY=여기에-OpenAI-키를-입력하세요
MCP_SERVER_URL=http://localhost:8001/mcp
```

## 실행 방법

1. 의존성 설치
   ```bash
   pip install -r requirements.txt
   ```
2. MCP 서버 실행
   ```bash
   uvicorn mcp_demo.mcp_server:app --port 8001
   ```
3. 예제 API 서버 실행 (또는 원하는 포트 지정)
   ```bash
   uvicorn main:app --port 8000
   ```
4. 브라우저에서 `http://localhost:8000` 에 접속하여 질문을 입력하면 GPT가 MCP 도구를 호출해 현재 시간을 알려줍니다.

### 직접 도구 호출 예시

MCP 서버에 직접 요청을 보내는 방법은 다음과 같습니다.

```bash
curl -X POST http://localhost:8001/mcp \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"get_current_time","params":{},"id":"1"}'
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
