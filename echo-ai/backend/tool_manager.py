import os
from typing import Dict, Any, List, Optional

# Import Phase 2 Services
from tools.filesystem.service import FilesystemService
from tools.notes.service import NotesService
from tools.pdf.service import PDFService
from tools.browser.service import BrowserService
from tools.system.service import SystemService
from tools.productivity.service import ProductivityService
from tools.gmail.service import GmailService
from tools.calendar.service import CalendarService
from tools.knowledge.service import KnowledgeService

# Import schemas for validation in tool manager
from tools.notes.schemas import NoteCreate, NoteUpdate
from tools.productivity.schemas import WordParagraph, SlideContent
from tools.gmail.schemas import EmailRequest, ReplyRequest
from tools.calendar.schemas import CreateEventRequest, UpdateEventRequest, ReminderRequest

class ToolManagerError(Exception):
    pass

class ToolManager:
    def __init__(self, base_dir: str = ".", notes_service: Optional[NotesService] = None):
        self.base_dir = os.path.abspath(base_dir)
        self.last_resolved_id = None
        self.last_resolved_title = None
        
        # Instantiate services
        self.filesystem_service = FilesystemService(base_dir=self.base_dir)
        self.notes_service = notes_service or NotesService()  # SQLite db path is inside echo-ai/database/echo_ai.db
        self.pdf_service = PDFService(base_dir=self.base_dir)
        self.browser_service = BrowserService(base_dir=self.base_dir)
        self.system_service = SystemService()
        self.productivity_service = ProductivityService(base_dir=self.base_dir)
        self.gmail_service = GmailService(base_dir=self.base_dir)
        self.calendar_service = CalendarService(base_dir=self.base_dir)
        self.knowledge_service = KnowledgeService()

    def execute_tool(self, tool: str, action: str, parameters: Dict[str, Any]) -> Any:
        """
        Dispatches tool actions directly to Phase 2 services.
        Validates parameters against service models prior to execution.
        """
        self.last_resolved_id = None
        self.last_resolved_title = None
        tool_lower = tool.lower()
        action_lower = action.lower()
        
        try:
            if tool_lower == "file":
                return self._execute_file(action_lower, parameters)
            elif tool_lower == "notes":
                return self._execute_notes(action_lower, parameters)
            elif tool_lower == "pdf":
                return self._execute_pdf(action_lower, parameters)
            elif tool_lower == "browser":
                return self._execute_browser(action_lower, parameters)
            elif tool_lower == "system":
                return self._execute_system(action_lower, parameters)
            elif tool_lower == "productivity":
                return self._execute_productivity(action_lower, parameters)
            elif tool_lower == "gmail":
                return self._execute_gmail(action_lower, parameters)
            elif tool_lower == "calendar":
                return self._execute_calendar(action_lower, parameters)
            elif tool_lower == "knowledge":
                return self._execute_knowledge(action_lower, parameters)
            elif tool_lower == "none":
                return parameters.get("message", "I am Echo AI. How can I assist you?")
            else:
                raise ToolManagerError(f"Unknown tool: '{tool}'")
        except Exception as e:
            if isinstance(e, ToolManagerError):
                raise
            raise ToolManagerError(f"Error executing {tool}.{action}: {str(e)}") from e

    def _execute_file(self, action: str, params: Dict[str, Any]) -> Any:
        if action == "find":
            return self.filesystem_service.find_files(
                path=params.get("path", ""),
                query=params.get("query", ""),
                recursive=params.get("recursive", True)
            )
        elif action == "create_folder":
            return self.filesystem_service.create_folder(path=params.get("path", ""))
        elif action == "rename":
            return self.filesystem_service.rename(
                path=params.get("path", ""),
                new_name=params.get("new_name", "")
            )
        elif action == "move":
            self.filesystem_service.move(
                src_path=params.get("src_path", ""),
                dest_path=params.get("dest_path", "")
            )
            return {"status": "success"}
        elif action == "copy":
            self.filesystem_service.copy(
                src_path=params.get("src_path", ""),
                dest_path=params.get("dest_path", "")
            )
            return {"status": "success"}
        elif action == "delete":
            self.filesystem_service.delete(path=params.get("path", ""))
            return {"status": "success"}
        elif action == "open":
            self.filesystem_service.open_file(path=params.get("path", ""))
            return {"status": "success"}
        elif action == "list":
            return self.filesystem_service.list_dir(path=params.get("path", ""))
        else:
            raise ToolManagerError(f"Unknown action for file tool: '{action}'")

    def _find_notes_by_title(self, title: str) -> List[Any]:
        """Finds notes matching title case-insensitively. Supports partial matches if exact doesn't exist."""
        if not title:
            return []
        target = title.strip().lower()
        all_notes = self.notes_service.list_notes()
        
        # 1. Look for exact matches
        exact_matches = [n for n in all_notes if n.title.strip().lower() == target]
        if exact_matches:
            return exact_matches
            
        # 2. Fallback to partial matches
        partial_matches = [n for n in all_notes if target in n.title.strip().lower()]
        return partial_matches

    def _execute_notes(self, action: str, params: Dict[str, Any]) -> Any:
        if action == "create":
            req = NoteCreate(**params)
            note = self.notes_service.create_note(req)
            self.last_resolved_id = note.id
            self.last_resolved_title = note.title
            return note
            
        elif action == "read":
            title = params.get("title")
            note_id = params.get("id")
            
            if note_id is not None:
                note = self.notes_service.get_note(int(note_id))
                if not note:
                    raise FileNotFoundError(f"Note with ID {note_id} not found.")
                self.last_resolved_id = note.id
                self.last_resolved_title = note.title
                return note
                
            if title is not None:
                if not title.strip():
                    raise ValueError("Note title cannot be empty.")
                matches = self._find_notes_by_title(title)
                if not matches:
                    raise FileNotFoundError(f"Note '{title}' not found.")
                if len(matches) == 1:
                    note = matches[0]
                    self.last_resolved_id = note.id
                    self.last_resolved_title = note.title
                    return note
                    
                # Multiple matches
                if params.get("fallback_to_newest") is True:
                    newest = sorted(matches, key=lambda x: x.updated_at, reverse=True)[0]
                    self.last_resolved_id = newest.id
                    self.last_resolved_title = newest.title
                    return newest
                    
                return {
                    "success": False,
                    "requires_clarification": True,
                    "message": f"I found {len(matches)} notes named '{title}'. Which one do you want?",
                    "options": [{"id": m.id, "title": m.title, "created_at": m.created_at} for m in matches]
                }
                
            return self.notes_service.list_notes()
            
        elif action == "update":
            title = params.get("title")
            note_id = params.get("id")
            resolved_id = None
            resolved_title = None
            
            if note_id is not None:
                resolved_id = int(note_id)
                # Fetch note to get title
                note = self.notes_service.get_note(resolved_id)
                if note:
                    resolved_title = note.title
            elif title is not None:
                if not title.strip():
                    raise ValueError("Note title cannot be empty.")
                matches = self._find_notes_by_title(title)
                if not matches:
                    raise FileNotFoundError(f"Note '{title}' not found.")
                if len(matches) == 1:
                    resolved_id = matches[0].id
                    resolved_title = matches[0].title
                else:
                    if params.get("fallback_to_newest") is True:
                        newest = sorted(matches, key=lambda x: x.updated_at, reverse=True)[0]
                        resolved_id = newest.id
                        resolved_title = newest.title
                    else:
                        return {
                            "success": False,
                            "requires_clarification": True,
                            "message": f"I found {len(matches)} notes named '{title}'. Which one do you want?",
                            "options": [{"id": m.id, "title": m.title, "created_at": m.created_at} for m in matches]
                        }
            else:
                raise ValueError("Missing parameter: 'title' or 'id' is required for update")
                
            if resolved_id is not None:
                self.last_resolved_id = resolved_id
                self.last_resolved_title = resolved_title
                
                # Remove title/id/fallback parameters from payload to avoid schema conflict
                update_data = {}
                if "content" in params:
                    update_data["content"] = params["content"]
                if "tags" in params:
                    update_data["tags"] = params["tags"]
                if "new_title" in params:
                    update_data["title"] = params["new_title"]
                    
                req = NoteUpdate(**update_data)
                note = self.notes_service.update_note(resolved_id, req)
                if not note:
                    raise FileNotFoundError(f"Note with ID {resolved_id} not found.")
                return note
                
        elif action == "delete":
            title = params.get("title")
            note_id = params.get("id")
            resolved_id = None
            resolved_title = None
            
            if note_id is not None:
                resolved_id = int(note_id)
                note = self.notes_service.get_note(resolved_id)
                if note:
                    resolved_title = note.title
            elif title is not None:
                if not title.strip():
                    raise ValueError("Note title cannot be empty.")
                matches = self._find_notes_by_title(title)
                if not matches:
                    raise FileNotFoundError(f"Note '{title}' not found.")
                if len(matches) == 1:
                    resolved_id = matches[0].id
                    resolved_title = matches[0].title
                else:
                    if params.get("fallback_to_newest") is True:
                        newest = sorted(matches, key=lambda x: x.updated_at, reverse=True)[0]
                        resolved_id = newest.id
                        resolved_title = newest.title
                    else:
                        return {
                            "success": False,
                            "requires_clarification": True,
                            "message": f"I found {len(matches)} notes named '{title}'. Which one do you want?",
                            "options": [{"id": m.id, "title": m.title, "created_at": m.created_at} for m in matches]
                        }
            else:
                raise ValueError("Missing parameter: 'title' or 'id' is required for delete")
                
            if resolved_id is not None:
                self.last_resolved_id = resolved_id
                self.last_resolved_title = resolved_title
                
                success = self.notes_service.delete_note(resolved_id)
                if not success:
                    raise FileNotFoundError(f"Note with ID {resolved_id} not found.")
                return {"status": "success"}
                
        elif action == "search":
            return self.notes_service.search_notes(query=params.get("q", ""))
        else:
            raise ToolManagerError(f"Unknown action for notes tool: '{action}'")

    def _execute_pdf(self, action: str, params: Dict[str, Any]) -> Any:
        if action == "read":
            return self.pdf_service.read_pdf(
                path=params.get("path", ""),
                page_range=params.get("page_range")
            )
        elif action == "search":
            return self.pdf_service.search_pdf(
                path=params.get("path", ""),
                query=params.get("query", "")
            )
        else:
            raise ToolManagerError(f"Unknown action for pdf tool: '{action}'")

    def _execute_browser(self, action: str, params: Dict[str, Any]) -> Any:
        if action == "search":
            return self.browser_service.google_search(
                query=params.get("query", ""),
                max_results=params.get("max_results", 10)
            )
        elif action == "read":
            return self.browser_service.read_page(url=params.get("url", ""))
        elif action == "download_pdf":
            return self.browser_service.download_pdf(
                url=params.get("url", ""),
                output_filename=params.get("output_filename")
            )
        else:
            raise ToolManagerError(f"Unknown action for browser tool: '{action}'")

    def _execute_system(self, action: str, params: Dict[str, Any]) -> Any:
        if action == "cpu":
            return self.system_service.cpu_usage()
        elif action == "memory":
            return self.system_service.memory_usage()
        elif action == "disk":
            return self.system_service.disk_usage(path=params.get("path"))
        elif action == "battery":
            return self.system_service.battery_status()
        elif action == "processes":
            return self.system_service.list_processes(limit=params.get("limit", 20))
        elif action == "apps":
            return self.system_service.get_installed_applications()
        elif action == "open":
            return self.system_service.open_application(
                app_name=params.get("app_name", ""),
                args=params.get("args")
            )
        elif action == "close":
            return self.system_service.close_application(app_name=params.get("app_name", ""))
        else:
            raise ToolManagerError(f"Unknown action for system tool: '{action}'")

    def _execute_productivity(self, action: str, params: Dict[str, Any]) -> Any:
        if action == "excel":
            return self.productivity_service.create_excel(
                path=params.get("path", ""),
                data=params.get("data", {})
            )
        elif action == "word":
            # Map input content into WordParagraph objects
            paragraphs_input = params.get("content", [])
            paragraphs = []
            for p in paragraphs_input:
                paragraphs.append(WordParagraph(**p))
            return self.productivity_service.create_word(
                path=params.get("path", ""),
                title=params.get("title", ""),
                paragraphs=paragraphs
            )
        elif action == "powerpoint":
            slides_input = params.get("slides", [])
            slides = []
            for s in slides_input:
                slides.append(SlideContent(**s))
            return self.productivity_service.create_ppt(
                path=params.get("path", ""),
                title=params.get("title", ""),
                subtitle=params.get("subtitle"),
                slides=slides
            )
        elif action == "csv_read":
            return self.productivity_service.read_csv(path=params.get("path", ""))
        else:
            raise ToolManagerError(f"Unknown action for productivity tool: '{action}'")

    def _execute_gmail(self, action: str, params: Dict[str, Any]) -> Any:
        if action == "unread":
            return self.gmail_service.read_emails(label="UNREAD", limit=params.get("limit", 10))
        elif action == "search":
            return self.gmail_service.search_emails(query=params.get("q", ""), limit=params.get("limit", 10))
        elif action == "message":
            return self.gmail_service.get_email(message_id=params.get("message_id", ""))
        elif action == "send":
            req = EmailRequest(**params)
            return self.gmail_service.send_email(req)
        elif action == "reply":
            msg_id = params.get("message_id")
            if not msg_id:
                raise ValueError("Missing parameter: 'message_id' is required for email reply")
            req = ReplyRequest(**params)
            return self.gmail_service.reply_email(msg_id, req)
        elif action == "archive":
            self.gmail_service.archive_email(message_id=params.get("message_id", ""))
            return {"status": "success"}
        elif action == "download_attachment":
            return self.gmail_service.download_attachment(
                message_id=params.get("message_id", ""),
                attachment_id=params.get("attachment_id", ""),
                filename=params.get("filename", "")
            )
        elif action == "delete":
            self.gmail_service.delete_email(message_id=params.get("message_id", ""))
            return {"status": "success"}
        else:
            raise ToolManagerError(f"Unknown action for gmail tool: '{action}'")

    def _execute_calendar(self, action: str, params: Dict[str, Any]) -> Any:
        if action == "today":
            return self.calendar_service.today_events()
        elif action == "search":
            return self.calendar_service.search_events(query=params.get("q", ""))
        elif action == "create":
            # Map reminders override structures if present
            reminders_in = params.get("reminders")
            reminders = None
            if reminders_in is not None:
                reminders = [ReminderRequest(**r) for r in reminders_in]
            
            req = CreateEventRequest(
                summary=params.get("summary", ""),
                description=params.get("description"),
                location=params.get("location"),
                start_time=params.get("start_time", ""),
                end_time=params.get("end_time", ""),
                attendees=params.get("attendees", []),
                reminders=reminders
            )
            return self.calendar_service.create_event(req)
        elif action == "update":
            event_id = params.get("event_id")
            if not event_id:
                raise ValueError("Missing parameter: 'event_id' is required for calendar update")
                
            reminders_in = params.get("reminders")
            reminders = None
            if reminders_in is not None:
                reminders = [ReminderRequest(**r) for r in reminders_in]
                
            req = UpdateEventRequest(
                summary=params.get("summary"),
                description=params.get("description"),
                location=params.get("location"),
                start_time=params.get("start_time"),
                end_time=params.get("end_time"),
                attendees=params.get("attendees"),
                reminders=reminders
            )
            return self.calendar_service.update_event(event_id, req)
        elif action == "move":
            event_id = params.get("event_id")
            if not event_id:
                raise ValueError("Missing parameter: 'event_id' is required to move a calendar event")
            return self.calendar_service.move_event(
                event_id=event_id,
                start_time=params.get("start_time", ""),
                end_time=params.get("end_time", "")
            )
        elif action == "delete":
            self.calendar_service.delete_event(event_id=params.get("event_id", ""))
            return {"status": "success"}
        elif action == "free_slots":
            return self.calendar_service.free_slots(
                start_time=params.get("start_time", ""),
                end_time=params.get("end_time", ""),
                duration_minutes=params.get("duration_minutes", 30)
            )
        else:
            raise ToolManagerError(f"Unknown action for calendar tool: '{action}'")

    def _execute_knowledge(self, action: str, params: Dict[str, Any]) -> Any:
        if action == "index_document":
            return self.knowledge_service.index_document(params.get("file_path", ""))
        elif action == "search":
            return self.knowledge_service.search(
                query=params.get("query", ""),
                file_path_filter=params.get("file_path_filter"),
                file_type_filter=params.get("file_type_filter")
            )
        elif action == "delete_document":
            return self.knowledge_service.delete_document(params.get("file_path", ""))
        elif action == "list_documents":
            return self.knowledge_service.list_documents()
        elif action == "reindex":
            return self.knowledge_service.reindex()
        elif action == "summarize_document":
            return self.knowledge_service.summarize_document(params.get("file_path", ""))
        else:
            raise ToolManagerError(f"Unknown action for knowledge tool: '{action}'")
