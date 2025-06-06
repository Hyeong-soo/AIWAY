"""Time utilities exposed as MCP tools."""

from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP

app = FastMCP(name="time-service")


@app.tool()
def get_current_time() -> str:
    """Return the current system time as an ISO string."""
    return datetime.now().isoformat()


@app.tool()
def calculate_discharge_date(start_date: str, service_days: int) -> str:
    """Return the date after completing the given number of service days."""
    start_dt = datetime.fromisoformat(start_date)
    discharge = start_dt + timedelta(days=service_days)
    return discharge.date().isoformat()


__all__ = ["app", "get_current_time", "calculate_discharge_date"]

