"""Sends mail through SMTP if MAIL_SERVER is set, otherwise just prints it (dev mode)."""
import os
import smtplib
from email.message import EmailMessage


def send_mail(to, subject, text, html=None):
    host = os.environ.get("MAIL_SERVER")
    if not host:
        print(f"[MAIL not configured] to={to} subject={subject}\n{text}\n")
        return False
    try:
        msg = EmailMessage()
        msg["From"] = os.environ.get("MAIL_FROM", "noreply@emp.local")
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(text)
        if html:
            msg.add_alternative(html, subtype="html")
        with smtplib.SMTP(host, int(os.environ.get("MAIL_PORT", 587)), timeout=10) as server:
            server.starttls()
            if os.environ.get("MAIL_USERNAME"):
                server.login(os.environ["MAIL_USERNAME"], os.environ.get("MAIL_PASSWORD", ""))
            server.send_message(msg)
        return True
    except Exception as err:
        print("mail failed:", err)
        return False
