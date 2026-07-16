import json
import os
from typing import Dict, Any, Optional
from backend.ai.llm import LLMService
from backend.planner.prompts import PLANNER_SYSTEM_PROMPT
from backend.planner.schemas import Plan, Task

class Planner:
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm_service = llm_service or LLMService()
        # Respect PLANNER_MODEL configuration if set
        planner_model = os.getenv("PLANNER_MODEL")
        if planner_model:
            self.llm_service.model_name = planner_model

    def generate_plan(self, user_message: str, memory_context: str = "") -> Plan:
        """
        Interacts with the LLM to generate an execution plan for a user query.
        Incorporates conversational memory to resolve pronouns and references.
        """
        combined_prompt = f"User Request: {user_message}\n"
        if memory_context:
            combined_prompt += f"\nConversation Memory Context (use this to resolve relative references):\n{memory_context}\n"

        raw_output = self.llm_service.generate_response(PLANNER_SYSTEM_PROMPT, combined_prompt)
        
        # Clean response of potential markdown tags
        cleaned = raw_output.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON format received from LLM: {str(e)}\nRaw Response: {raw_output}"
            ) from e

        # Standardize single-step or flat list responses into a standard Plan steps schema
        if not isinstance(data, dict):
            if isinstance(data, list):
                data = {"steps": data}
            else:
                raise ValueError("Planner response is not a valid JSON structure")

        if "steps" not in data:
            # Check if it was returned as a single flat task
            if "tool" in data and "action" in data:
                if "step" not in data:
                    data["step"] = 1
                data = {"steps": [data]}
            else:
                raise ValueError("Planner response missing required 'steps' list")

        # Automatically populate missing 'step' field and flatten parameters in list elements
        if "steps" in data and isinstance(data["steps"], list):
            for idx, task_data in enumerate(data["steps"]):
                if isinstance(task_data, dict):
                    if "step" not in task_data:
                        task_data["step"] = idx + 1
                    
                    # Ensure 'parameters' dictionary is present
                    if "parameters" not in task_data:
                        task_data["parameters"] = {}
                        
                    # Flatten top-level keys into parameters dictionary
                    for k, v in list(task_data.items()):
                        if k not in ("step", "tool", "action", "dependencies", "parameters"):
                            task_data["parameters"][k] = v
                            del task_data[k]

        try:
            return Plan(**data)
        except Exception as e:
            err_msg = str(e)
            if "steps.0.tool" in err_msg or "steps.0.tool" in err_msg.lower():
                err_msg = f"Unknown tool: {err_msg}"
            elif "steps.0.action" in err_msg or "steps.0.action" in err_msg.lower():
                err_msg = f"Unknown action: {err_msg}"
            raise ValueError(f"Planner response validation failed against schema: {err_msg}") from e
