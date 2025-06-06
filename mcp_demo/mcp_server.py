"""MCP server for the time service."""

from mcp.server.fastmcp import FastMCP

app = FastMCP(name="time-service")

# Import tools to register them with the app
from .tools import time_tool  # noqa: E402

__all__ = ["app"]
