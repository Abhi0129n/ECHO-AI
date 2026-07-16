import time
import logging
from typing import Any, Dict, Optional
from backend.tool_manager import ToolManager, ToolManagerError
from backend.planner.schemas import Task

logger = logging.getLogger("echo_ai.executor")

class Executor:
    def __init__(self, tool_manager: ToolManager, max_retries: int = 3):
        self.tool_manager = tool_manager
        self.max_retries = max_retries

    def execute_task(self, task: Task, resolved_params: Dict[str, Any]) -> Any:
        """
        Executes a single planned task using ToolManager.
        Wraps transient error handling and automatic retry logic.
        """
        attempts = 0
        backoff = 1.0  # Seconds
        
        while True:
            try:
                # Dispatch the call to tool manager
                result = self.tool_manager.execute_tool(task.tool, task.action, resolved_params)
                return result
            except Exception as e:
                attempts += 1
                
                # Assess if error is transient (network, timeout, rate limit) or validation/not found
                if self._is_transient(e) and attempts <= self.max_retries:
                    logger.warning(
                        f"Transient error on step {task.step} ({task.tool}.{task.action}): {str(e)}. "
                        f"Retrying attempt {attempts}/{self.max_retries} in {backoff}s..."
                    )
                    time.sleep(backoff)
                    backoff *= 2.0  # Exponential backoff
                    continue
                    
                # Reraise permanent failures or exhausted retries
                raise e

    def _is_transient(self, e: Exception) -> bool:
        """Classifies if an exception represents a temporary retryable system issue."""
        err_str = str(e).lower()
        
        # Exclude permanent validation / missing resource errors
        if isinstance(e, (FileNotFoundError, PermissionError, ValueError, KeyError, IndexError, TypeError, AttributeError)):
            return False
            
        # Check exception types
        if isinstance(e, (TimeoutError, ConnectionError, OSError)):
            # On Windows, some OSErrors could be transient, but we also rely on string matching
            return True
            
        transient_keywords = [
            "timeout", "timed out", "rate limit", "too many requests", 
            "network", "connection failed", "temporary failure", 
            "503", "502 bad gateway", "bad gateway", "service unavailable"
        ]
        
        for kw in transient_keywords:
            if kw in err_str:
                return True
                
        return False
