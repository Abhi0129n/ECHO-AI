import json
from typing import Dict, Any
from backend.ai.schemas import IntentSchema

class JSONParserError(Exception):
    """Custom exception raised when JSON parsing or schema validation fails."""
    pass

class JSONParser:
    @staticmethod
    def parse_intent(raw_text: str) -> IntentSchema:
        """
        Cleans, parses, and validates the LLM response.
        Extracts tool name, action name, and parameters dictionary.
        """
        cleaned = raw_text.strip()
        
        # Strip potential markdown enclosures (e.g. ```json ... ```)
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
            raise JSONParserError(f"Invalid JSON format received from LLM: {str(e)}") from e

        if not isinstance(data, dict):
            raise JSONParserError("Parsed JSON output is not a dictionary structure")

        if "tool" not in data or "action" not in data:
            raise JSONParserError("Missing required 'tool' or 'action' fields in JSON")

        if "parameters" not in data:
            data["parameters"] = {}
        elif not isinstance(data["parameters"], dict):
            raise JSONParserError("'parameters' field must be a dictionary")

        # Flatten any top-level parameters (e.g. title, content, tags) into parameters dictionary
        for k, v in data.items():
            if k not in ("tool", "action", "parameters"):
                data["parameters"][k] = v

        try:
            return IntentSchema(
                tool=data["tool"],
                action=data["action"],
                parameters=data["parameters"]
            )
        except Exception as e:
            raise JSONParserError(f"Intent validation failed against schema: {str(e)}") from e
