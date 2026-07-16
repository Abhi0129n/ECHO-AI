import time
import json
import os
from datetime import datetime, timezone
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

LOGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logs"))

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Get path and determine tool name
        path = request.url.path
        tool_name = "core"
        parts = path.strip("/").split("/")
        if parts:
            tool_name = parts[0]
            
        success = True
        error_detail = None
        response = None
        
        try:
            response = await call_next(request)
            if response.status_code >= 400:
                success = False
            return response
        except Exception as e:
            success = False
            error_detail = str(e)
            raise e
        finally:
            execution_time = (time.time() - start_time) * 1000  # in ms
            status_code = response.status_code if response else 500
            
            # Format log entry
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_action": f"{request.method} {path}",
                "tool_name": tool_name,
                "execution_time_ms": round(execution_time, 2),
                "success": success,
                "status_code": status_code
            }
            if error_detail:
                log_entry["error_detail"] = error_detail
            elif status_code >= 400:
                log_entry["error_detail"] = f"HTTP status {status_code}"
                
            os.makedirs(LOGS_DIR, exist_ok=True)
            log_file = os.path.join(LOGS_DIR, "echo_ai.log")
            
            try:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception:
                # Fallback to stdout if log file write fails
                print(f"Failed to write log entry: {log_entry}")
