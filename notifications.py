"""Outbound email/SMS notifications for AnythingGPT.

Configure via environment variables (put them in a local .env file, see .env.example):

  EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD, EMAIL_FROM   -- SMTP settings
  TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER        -- SMS via Twilio (optional)

If EMAIL_* is not configured, send_email() logs to the console instead of failing,
so the app still works locally without a real mail server.
"""
import os
import smtplib
from email.message import EmailMessage

try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    pass


def send_email(to_address: str, subject: str, body: str) -> bool:
    host = os.getenv("EMAIL_HOST")
    port = os.getenv("EMAIL_PORT", "587")
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASSWORD")
    sender = os.getenv("EMAIL_FROM", user)

    if not (host and user and password and sender):
        # No SMTP configured: fall back to a console log so local dev/testing still works.
        print(f"[notifications] (SMTP not configured) would email {to_address}: {subject}\n{body}")
        return True

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = to_address
        msg.set_content(body)
        with smtplib.SMTP(host, int(port), timeout=10) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
        return True
    except Exception as exc:
        print(f"[notifications] Failed to send email to {to_address}: {exc}")
        return False


def send_sms(to_number: str, body: str) -> bool:
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")

    if not (sid and token and from_number):
        print(f"[notifications] (SMS not configured) would text {to_number}: {body}")
        return True

    try:
        from twilio.rest import Client
    except ModuleNotFoundError:
        print("[notifications] Install the 'twilio' package to enable real SMS sending.")
        return False

    try:
        Client(sid, token).messages.create(to=to_number, from_=from_number, body=body)
        return True
    except Exception as exc:
        print(f"[notifications] Failed to send SMS to {to_number}: {exc}")
        return False
