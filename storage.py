import json
import uuid
from datetime import datetime
from pathlib import Path

BASE = Path("data/conversations")


def _path(username):
    path = BASE / f"{username}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _load(username):
    path = _path(username)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def _save(username, chats):
    _path(username).write_text(json.dumps(chats, ensure_ascii=False, indent=2), encoding="utf-8")


def list_conversations(username):
    return sorted(_load(username), key=lambda chat: chat["updated_at"], reverse=True)


def create_conversation(username, title, messages):
    chat_id = uuid.uuid4().hex
    chats = _load(username)
    chats.append({"id": chat_id, "title": title, "messages": messages, "updated_at": datetime.now().isoformat(timespec="seconds")})
    _save(username, chats)
    return chat_id


def get_conversation(username, chat_id):
    return next((chat for chat in _load(username) if chat["id"] == chat_id), None)


def save_conversation(username, chat_id, messages):
    chats = _load(username)
    for chat in chats:
        if chat["id"] == chat_id:
            chat["messages"] = messages
            chat["updated_at"] = datetime.now().isoformat(timespec="seconds")
    _save(username, chats)


def delete_conversation(username, chat_id):
    _save(username, [chat for chat in _load(username) if chat["id"] != chat_id])
