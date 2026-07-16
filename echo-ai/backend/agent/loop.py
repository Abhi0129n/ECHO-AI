import time
from typing import Callable, Dict, Any, Optional
from backend.planner.schemas import Plan, Task
from backend.agent.context import ExecutionContext
from backend.agent.executor import Executor

class AgentLoop:
    def __init__(
        self,
        executor: Executor,
        max_steps: int = 10,
        timeout: float = 30.0,
        progress_callback: Optional[Callable[[str], None]] = None
    ):
        self.executor = executor
        self.max_steps = max_steps
        self.timeout = timeout
        self.progress_callback = progress_callback

    def run(
        self, 
        plan: Plan, 
        start_step_idx: int = 0, 
        context: Optional[ExecutionContext] = None
    ) -> Dict[str, Any]:
        """
        Executes planned tasks sequentially, performing variable resolutions,
        progress reporting, timeouts, step limits, and clarification handling.
        """
        if context is None:
            context = ExecutionContext()

        start_time = time.time()
        steps = plan.steps
        steps_count = len(steps)
        steps_executed = 0
        step_idx = start_step_idx

        self._report_progress("Planning complete. Beginning execution...")

        while step_idx < steps_count:
            # 1. Enforce step limit
            if steps_executed >= self.max_steps:
                raise RuntimeError(
                    f"Agent execution aborted: Exceeded configured limit of {self.max_steps} steps."
                )

            # 2. Enforce total timeout
            elapsed = time.time() - start_time
            if elapsed > self.timeout:
                raise TimeoutError(
                    f"Agent execution timed out: Exceeded {self.timeout}s budget by {elapsed - self.timeout:.2f}s."
                )

            task = steps[step_idx]
            
            # Format and notify progress
            action_desc = f"{task.tool.capitalize()} Tool: {task.action.replace('_', ' ')}"
            self._report_progress(f"Running step {task.step}/{steps_count}: {action_desc}...")

            # 3. Resolve context parameters
            resolved_params = context.resolve_parameters(task.parameters)

            # 4. Dispatch and execute task
            result = self.executor.execute_task(task, resolved_params)

            # 5. Clarification Intercept
            if isinstance(result, dict) and result.get("requires_clarification") is True:
                self._report_progress(f"Execution paused at step {task.step}. Awaiting user clarification...")
                return {
                    "status": "clarification",
                    "requires_clarification": True,
                    "message": result.get("message"),
                    "options": result.get("options"),
                    "pending_step_idx": step_idx,
                    "context": context,
                    "plan": plan
                }

            # 6. Store output
            context.set_step_output(task.step, result)
            
            steps_executed += 1
            step_idx += 1

        self._report_progress("All planned steps completed successfully.")

        # Extract final step's output to return
        final_result = None
        if steps:
            final_result = context.outputs.get(steps[-1].step)

        return {
            "status": "completed",
            "result": final_result,
            "context": context
        }

    def _report_progress(self, msg: str) -> None:
        if self.progress_callback:
            self.progress_callback(msg)
