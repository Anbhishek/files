"""Simple local-only authentication for AnythingGPT."""
import hashlib
import json
import re
import secrets
from datetime import datetime, timedelta
from pathlib import Path

from notifications import send_email, send_sms

DATA_FILE = Path("data/users.json")
RESET_CODE_TTL_MINUTES = 15
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _load():
    DATA_FILE.parent.mkdir(exist_ok=True)
    return json.loads(DATA_FILE.read_text(encoding="utf-8")) if DATA_FILE.exists() else {}


def _save(users):
    DATA_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")


def _hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 310_000).hex()


def create_user(display_name, username, password, email="", phone=""):
    username = username.strip().lower()
    email = email.strip().lower()
    phone = phone.strip()
    users = _load()
    if len(display_name.strip()) < 2 or len(username) < 3 or len(password) < 6:
        return False, "Use a name, a 3+ character username, and a 6+ character password."
    if username in users:
        return False, "That username is already in use."
    if email and not EMAIL_RE.match(email):
        return False, "That doesn't look like a valid email address."
    salt = secrets.token_hex(16)
    users[username] = {
        "display_name": display_name.strip(),
        "salt": salt,
        "password_hash": _hash(password, salt),
        "email": email,
        "phone": phone,
        "reset_code_hash": None,
        "reset_code_expires": None,
    }
    _save(users)

    # Let the user know their account was created, on whichever channel they gave us.
    # We never send the password itself -- only a confirmation.
    if email:
        send_email(
            email,
            "Your AnythingGPT account was created",
            f"Hi {display_name.strip()},\n\nYour AnythingGPT account '{username}' was just created on this device.\n"
            "If this wasn't you, no action is needed since this app only stores data locally.",
        )
    if phone:
        send_sms(phone, f"AnythingGPT: your account '{username}' was created.")

    return True, "Account created. You can now sign in."


def login_user(username, password):
    user = _load().get(username.strip().lower())
    if user and secrets.compare_digest(user["password_hash"], _hash(password, user["salt"])):
        return {"username": username.strip().lower(), "display_name": user["display_name"]}
    return None


def get_user(username):
    return _load().get(username.strip().lower())


def update_profile(username, email=None, phone=None):
    users = _load()
    user = users.get(username)
    if not user:
        return False, "Account not found."
    if email is not None:
        email = email.strip().lower()
        if email and not EMAIL_RE.match(email):
            return False, "That doesn't look like a valid email address."
        user["email"] = email
    if phone is not None:
        user["phone"] = phone.strip()
    _save(users)
    return True, "Profile updated."


def change_password(username, current_password, new_password):
    users = _load()
    user = users.get(username)
    if not user or not secrets.compare_digest(user["password_hash"], _hash(current_password, user["salt"])):
        return False, "Current password is incorrect."
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters."
    salt = secrets.token_hex(16)
    user["salt"] = salt
    user["password_hash"] = _hash(new_password, salt)
    _save(users)
    return True, "Password changed."


def request_password_reset(username, channel="email"):
    """Generate a one-time reset code and deliver it via email or SMS.

    We only ever send a short-lived random code, never the real password.
    """
    users = _load()
    username = username.strip().lower()
    user = users.get(username)
    if not user:
        # Don't reveal whether the account exists.
        return True, "If that account exists, a reset code has been sent."

    destination = user.get("email") if channel == "email" else user.get("phone")
    if not destination:
        return False, f"No {channel} is on file for this account. Add one in Account settings first."

    code = f"{secrets.randbelow(1_000_000):06d}"
    user["reset_code_hash"] = hashlib.sha256(code.encode()).hexdigest()
    user["reset_code_expires"] = (datetime.now() + timedelta(minutes=RESET_CODE_TTL_MINUTES)).isoformat()
    _save(users)

    message = f"Your AnythingGPT password reset code is {code}. It expires in {RESET_CODE_TTL_MINUTES} minutes."
    ok = send_email(destination, "Your AnythingGPT reset code", message) if channel == "email" else send_sms(destination, message)
    if not ok:
        return False, f"Couldn't send the code via {channel}. Check the notification settings."
    return True, "If that account exists, a reset code has been sent."


def reset_password(username, code, new_password):
    users = _load()
    username = username.strip().lower()
    user = users.get(username)
    if not user or not user.get("reset_code_hash"):
        return False, "No reset was requested for this account."
    if datetime.now() > datetime.fromisoformat(user["reset_code_expires"]):
        return False, "That code has expired. Request a new one."
    if not secrets.compare_digest(user["reset_code_hash"], hashlib.sha256(code.encode()).hexdigest()):
        return False, "Incorrect code."
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters."
    salt = secrets.token_hex(16)
    user["salt"] = salt
    user["password_hash"] = _hash(new_password, salt)
    user["reset_code_hash"] = None
    user["reset_code_expires"] = None
    _save(users)
    return True, "Password reset. You can now sign in."
