import re
import json
from typing import Any, Dict, List, Optional

class ExecutionContext:
    def __init__(self):
        # Maps step number (int) to execution output (Any)
        self.outputs: Dict[int, Any] = {}

    def set_step_output(self, step: int, output: Any) -> None:
        """Stores the output of a specific step."""
        self.outputs[step] = output

    def resolve_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively parses and resolves placeholders in a parameters dictionary."""
        return self._resolve(params)

    def _resolve(self, val: Any) -> Any:
        if isinstance(val, dict):
            return {k: self._resolve(v) for k, v in val.items()}
        elif isinstance(val, list):
            return [self._resolve(v) for v in val]
        elif isinstance(val, str):
            return self._resolve_string(val)
        return val

    def _resolve_string(self, val: str) -> Any:
        # Match exactly "$stepX_result" or "$stepX_result.field"
        pattern_exact = re.compile(r'^\$step(\d+)_result(?:\.(\w+))?$')
        match_exact = pattern_exact.match(val)
        if match_exact:
            step_num = int(match_exact.group(1))
            subfield = match_exact.group(2)
            return self._get_step_val(step_num, subfield)

        # Match exact short form "$stepX" or "$stepX.field"
        pattern_exact_short = re.compile(r'^\$step(\d+)(?:\.(\w+))?$')
        match_exact_short = pattern_exact_short.match(val)
        if match_exact_short:
            step_num = int(match_exact_short.group(1))
            subfield = match_exact_short.group(2)
            return self._get_step_val(step_num, subfield)

        # Handle placeholders embedded within longer strings
        def replacer(match) -> str:
            step_num = int(match.group(1))
            subfield = match.group(2)
            step_val = self._get_step_val(step_num, subfield)
            
            # If the resolved value is dict or list, serialize it into a string
            if isinstance(step_val, (dict, list)):
                return json.dumps(step_val)
            return str(step_val) if step_val is not None else ""

        pattern_sub = re.compile(r'\$step(\d+)_result(?:\.(\w+))?')
        val_sub = pattern_sub.sub(replacer, val)
        
        pattern_sub_short = re.compile(r'\$step(\d+)(?:\.(\w+))?')
        return pattern_sub_short.sub(replacer, val_sub)

    def _get_step_val(self, step_num: int, subfield: Optional[str]) -> Any:
        if step_num not in self.outputs:
            return None
            
        output = self.outputs[step_num]
        
        # If a subfield is referenced (e.g. $step1_result.id)
        if subfield:
            if isinstance(output, dict):
                return output.get(subfield)
            elif hasattr(output, "model_dump"):
                # Pydantic model serialization support
                return output.model_dump().get(subfield)
            elif hasattr(output, subfield):
                return getattr(output, subfield)
                
        return output
