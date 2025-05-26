import json
import logging
import uuid
from datetime import datetime
from pathlib import Path


class ChatLog:
    """Not currently used, but a utility library to save conversation texts to a local file."""

    def __init__(self, log_dir: Path, filename: str = ""):
        if filename == "":
            # use today's date
            curr_date_str = datetime.now().strftime("%Y%m%d")
            filename = f"chat_log_{curr_date_str}.ndjson"
        self.log_dir = log_dir
        self.filename = filename
        self.log_file = self.log_dir / self.filename
        self.logger = logging.getLogger("brain_wave.chat_db.ChatLog")
        self.chat_id_dict = None

    def log_chat_completion(self, chat_id: str, messages_list: list[dict], completion_dict: dict):
        combined = {
            "chat_id": chat_id,
            "messages": messages_list,
            "completion": completion_dict,
            "logged_timestamp": datetime.now().timestamp(),
        }
        self.log_dict(combined)

    def log_dict(self, dict_to_log: dict):
        with open(self.log_file, "a") as outfile:
            outfile.write(json.dumps(dict_to_log) + "\n")

    def list_previous_logs(self, pattern: str = "*.ndjson"):
        previous_log_filepaths = []
        for filepath in self.log_dir.glob(pattern):
            previous_log_filepaths.append(self.log_dir / filepath)
        return previous_log_filepaths

    def load_previous_chats(self, use_cached: bool = True) -> dict:
        """Loads previous chats.

        Args:
            use_cached (bool, optional): If previously-loaded chats should be used. Defaults to True.

        Returns:
            dict: Map of chat_id -> saved contents dict
        """
        if self.chat_id_dict is not None and use_cached:
            return self.chat_id_dict
        previous_log_filepaths = self.list_previous_logs()
        self.logger.info(f"Identified {len(previous_log_filepaths)} log files.")
        chat_id_dict = {}
        for log_filepath in previous_log_filepaths:
            with open(log_filepath) as infile:
                for line in infile:
                    d = json.loads(line)
                    if "chat_id" not in d:
                        continue
                    chat_id = d["chat_id"]
                    if chat_id not in chat_id_dict or d["logged_timestamp"] > chat_id_dict[chat_id]["logged_timestamp"]:
                        # take the most recent chat_id info
                        chat_id_dict[chat_id] = d
        self.chat_id_dict = chat_id_dict
        return self.chat_id_dict

    def get_matching_chat_ids(self, messages: list[dict]):
        assert len(messages) > 0, "Continuation expects at least one initial message."
        matching_chat_ids = []
        for saved_chat in self.chat_id_dict.values():
            if saved_chat["messages"][: len(messages)] == messages:
                matching_chat_ids.append(saved_chat["chat_id"])
        return matching_chat_ids


def generate_chat_id():
    curr_date = datetime.now().strftime("%Y%m%d")
    curr_timestamp = datetime.now().timestamp()
    return f"{uuid.uuid4()}_{curr_date}_{curr_timestamp}"

def get_chat_by_id(self, chat_id: str) -> dict:
        """Retrieve a specific chat session by its ID.
        
        Args:
            chat_id (str): The unique identifier of the chat session
            
        Returns:
            dict: The complete chat session data including messages and completion
            None: If no chat with the given ID is found
        """
        if self.chat_id_dict is None:
            self.load_previous_chats()
        return self.chat_id_dict.get(chat_id)

    def search_chats(self, keyword: str, field: str = "content") -> list[dict]:
        """Search through all logged chats for messages containing the keyword.
        
        Args:
            keyword (str): The search term to look for
            field (str): Which message field to search in ('content', 'role', etc.)
            
        Returns:
            list[dict]: List of matching chat sessions (complete session data)
        """
        matches = []
        chats = self.load_previous_chats()
        
        for chat in chats.values():
            for message in chat["messages"]:
                if field in message and keyword.lower() in str(message[field]).lower():
                    matches.append(chat)
                    break  # Only need one match per chat session
        
        return matches

    def get_chat_statistics(self) -> dict:
        """Calculate basic statistics about stored chat sessions.
        
        Returns:
            dict: Statistics including:
                - total_sessions: Total number of chat sessions
                - total_messages: Combined count of all messages
                - earliest_date: Date of oldest session
                - latest_date: Date of most recent session
                - avg_messages: Average messages per session
        """
        stats = {
            "total_sessions": 0,
            "total_messages": 0,
            "earliest_date": None,
            "latest_date": None,
            "avg_messages": 0
        }
        
        chats = self.load_previous_chats()
        if not chats:
            return stats
            
        stats["total_sessions"] = len(chats)
        message_counts = []
        timestamps = []
        
        for chat in chats.values():
            msg_count = len(chat["messages"])
            stats["total_messages"] += msg_count
            message_counts.append(msg_count)
            timestamps.append(chat["logged_timestamp"])
            
        stats["earliest_date"] = datetime.fromtimestamp(min(timestamps)).isoformat()
        stats["latest_date"] = datetime.fromtimestamp(max(timestamps)).isoformat()
        stats["avg_messages"] = sum(message_counts) / len(message_counts)
        
        return stats

    def export_to_html(self, output_path: Path, chat_id: str = None):
        """Export chat logs to HTML format for better readability.
        
        Args:
            output_path (Path): Where to save the HTML file
            chat_id (str, optional): Specific chat to export. If None, exports all.
        """
        chats_to_export = []
        
        if chat_id:
            chat = self.get_chat_by_id(chat_id)
            if chat:
                chats_to_export.append(chat)
        else:
            chats_to_export = list(self.load_previous_chats().values())
            
        if not chats_to_export:
            self.logger.warning("No chats found to export")
            return
            
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Chat Logs Export</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; }
                .chat { border: 1px solid #ddd; margin-bottom: 20px; padding: 15px; border-radius: 5px; }
                .message { margin-bottom: 10px; }
                .user { color: #0066cc; font-weight: bold; }
                .assistant { color: #009933; font-weight: bold; }
                .timestamp { color: #666; font-size: 0.8em; }
                .chat-id { font-size: 0.9em; color: #888; }
            </style>
        </head>
        <body>
            <h1>Chat Logs Export</h1>
        """
        
        for chat in chats_to_export:
            html_content += f"""
            <div class="chat">
                <div class="chat-id">Chat ID: {chat['chat_id']}</div>
                <div class="timestamp">Logged: {datetime.fromtimestamp(chat['logged_timestamp']).isoformat()}</div>
            """
            
            for message in chat["messages"]:
                role_class = "user" if message["role"] == "user" else "assistant"
                html_content += f"""
                <div class="message {role_class}">
                    <span class="role">{message['role'].title()}:</span>
                    <span class="content">{message['content']}</span>
                </div>
                """
                
            html_content += "</div>"
            
        html_content += "</body></html>"
        
        with open(output_path, "w") as f:
            f.write(html_content)
            
        self.logger.info(f"Exported {len(chats_to_export)} chats to {output_path}")

    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Delete log files older than specified number of days.
        
        Args:
            days_to_keep (int): Number of days worth of logs to preserve
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_files = 0
        
        for log_file in self.list_previous_logs():
            file_date = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_date < cutoff_date:
                try:
                    log_file.unlink()
                    deleted_files += 1
                except Exception as e:
                    self.logger.error(f"Failed to delete {log_file}: {str(e)}")
                    
        self.logger.info(f"Deleted {deleted_files} old log files")
        return deleted_files
