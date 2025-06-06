# aiway

This project demonstrates simple time utilities exposed as tools via the
Model Context Protocol (MCP).

## Service utilities

The package `mcp_demo` contains the MCP server and its tools.

`tools/time_tool.py` defines two utilities:
- `get_current_time()` returns the current system time as an ISO string.
- `calculate_discharge_date(start_date, service_days)` returns the discharge
  date after the given number of service days.

## Example

Run `python3 main.py` to start the FastAPI-based MCP server. It listens on
`http://localhost:8000`. Tools can then be invoked by sending JSON-RPC requests
to the `/mcp` endpoint. For quick testing you can
call the functions directly in Python:

```python
from mcp_demo.tools.time_tool import get_current_time, calculate_discharge_date

print(get_current_time())
print(calculate_discharge_date("2023-01-01", 540))
```

To invoke the tool over HTTP:

```bash
curl -X POST http://localhost:8000/mcp \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc": "2.0", "method": "get_current_time", "params": {}, "id": "1"}'
```

