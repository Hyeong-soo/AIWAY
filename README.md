# aiway

This project demonstrates simple time utilities exposed as tools via the
Model Context Protocol (MCP).

## Service utilities

The module `service.py` defines an MCP `FastMCP` server with two tools:

- `get_current_time()` returns the current system time as an ISO string.
- `calculate_discharge_date(start_date, service_days)` returns the discharge
  date after the given number of service days.

## Example

Run `python3 main.py` to start the MCP server using the default stdio
transport. Tools can then be invoked by an MCP client. For quick testing you can
call the functions directly in Python:

```python
from service import get_current_time, calculate_discharge_date

print(get_current_time())
print(calculate_discharge_date("2023-01-01", 540))
```

