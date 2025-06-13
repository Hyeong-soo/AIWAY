import re
import os
import sys
import pytest
from httpx import AsyncClient, ASGITransport

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mcp_demo.mcp_server import app

@pytest.mark.asyncio
async def test_get_current_time():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        payload = {
            "jsonrpc": "2.0",
            "method": "get_current_time",
            "params": {},
            "id": "1"
        }
        resp = await ac.post("/mcp", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "result" in data
    assert "time" in data["result"]
    assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", data["result"]["time"])
