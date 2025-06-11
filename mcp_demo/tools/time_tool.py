"""Time utilities exposed as MCP tools."""

from datetime import datetime
import pytz

def get_current_time(params):  # 반드시 인자 하나 있어야 함
    now = datetime.now(pytz.timezone("Asia/Seoul"))
    return {
        "time": now.strftime("%Y-%m-%d %H:%M:%S")
    }




__all__ = ["get_current_time"]
