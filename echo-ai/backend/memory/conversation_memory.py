from typing import Dict, Any, Optional

class ConversationMemory:
    def __init__(self):
        self.last_note: Optional[str] = None
        self.last_file: Optional[str] = None
        self.last_email: Optional[str] = None
        self.last_pdf: Optional[str] = None
        self.last_browser_search: Optional[str] = None
        self.last_calendar_event: Optional[str] = None
        self.last_created_object: Optional[Dict[str, Any]] = None

    def update(self, tool: str, action: str, params: Dict[str, Any], result: Any) -> None:
        """
        Updates memory states based on execution outputs and input parameters.
        Tracks the latest interactable files, notes, emails, and objects.
        """
        tool_lower = tool.lower()
        action_lower = action.lower()

        # 1. Notes
        if tool_lower == "notes":
            title = params.get("title")
            if not title:
                if isinstance(result, dict):
                    title = result.get("title")
                elif hasattr(result, "title"):
                    title = result.title
            if title:
                self.last_note = title
                if action_lower == "create":
                    self.last_created_object = {"type": "note", "key": title}

        # 2. Files
        elif tool_lower == "file":
            path = params.get("path") or params.get("dest_path") or params.get("src_path")
            if path:
                self.last_file = path
                if action_lower == "create_folder":
                    self.last_created_object = {"type": "folder", "key": path}

        # 3. PDF
        elif tool_lower == "pdf":
            path = params.get("path")
            if path:
                self.last_pdf = path

        # 4. Gmail
        elif tool_lower == "gmail":
            recipient = params.get("recipient")
            if recipient:
                self.last_email = recipient
                if action_lower == "send":
                    self.last_created_object = {"type": "email", "key": recipient}

        # 5. Calendar
        elif tool_lower == "calendar":
            summary = params.get("summary")
            if summary:
                self.last_calendar_event = summary
                if action_lower == "create":
                    self.last_created_object = {"type": "calendar_event", "key": summary}

        # 6. Browser Search
        elif tool_lower == "browser":
            query = params.get("query")
            if query:
                self.last_browser_search = query

    def to_prompt_context(self) -> str:
        """Serializes current memory references into a prompt-injectable string."""
        lines = []
        if self.last_note:
            lines.append(f"- Last Note Title: {self.last_note}")
        if self.last_file:
            lines.append(f"- Last File Path: {self.last_file}")
        if self.last_email:
            lines.append(f"- Last Email Recipient: {self.last_email}")
        if self.last_pdf:
            lines.append(f"- Last PDF Path: {self.last_pdf}")
        if self.last_browser_search:
            lines.append(f"- Last Browser Search Query: {self.last_browser_search}")
        if self.last_calendar_event:
            lines.append(f"- Last Calendar Event: {self.last_calendar_event}")
        if self.last_created_object:
            obj_type = self.last_created_object["type"]
            obj_key = self.last_created_object["key"]
            lines.append(f"- Last Created Object: {obj_type} with key '{obj_key}'")

        if not lines:
            return "No previous conversation memory references available."
        return "\n".join(lines)
