"""
Email delivery via Gmail SMTP.

Gmail requires an App Password (not your normal login password) for SMTP
when 2FA is enabled, which it should be. See README for setup steps.
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger("strategy_agent.email")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
RECIPIENT = "sonwabo@edpartner.co.za"


def send_report(html_body: str, subject: str):
    sender = os.environ["GMAIL_ADDRESS"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = RECIPIENT
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(sender, app_password)
        server.sendmail(sender, [RECIPIENT], msg.as_string())

    logger.info("Report emailed to %s", RECIPIENT)
