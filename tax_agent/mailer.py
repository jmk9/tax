"""SMTP 이메일 발송. 비밀번호는 환경변수 SMTP_PASSWORD (Gmail 앱 비밀번호)."""
import os
import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate


def send_email(smtp_cfg: dict, to_addr: str, subject: str, body: str) -> None:
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = smtp_cfg["username"]
    msg["To"] = to_addr
    msg["Date"] = formatdate(localtime=True)

    password = os.environ.get("SMTP_PASSWORD")
    if not password:
        raise RuntimeError("SMTP_PASSWORD 환경변수가 설정되지 않았습니다")

    host = smtp_cfg.get("host", "smtp.gmail.com")
    port = smtp_cfg.get("port", 465)
    with smtplib.SMTP_SSL(host, port, timeout=30) as server:
        server.login(smtp_cfg["username"], password)
        server.sendmail(smtp_cfg["username"], [to_addr], msg.as_string())
