import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_escalation_email(escalation_id, conversation_id, activity_requested, user_message):
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    supervisor_email = os.getenv("SUPERVISOR_EMAIL", "bahaayyadcs@gmail.com")

    if not smtp_user or not smtp_password:
        print(f"No SMTP credentials, skipping email for {escalation_id}")
        return True

    subject = f"[Escalation {escalation_id}] Unavailable activity request"
    body = f"""
    <html><body>
        <h2>Allout Travel - Escalation</h2>
        <p>A customer requested something we don't have available.</p>
        <table>
            <tr><td><b>Ref:</b></td><td>{escalation_id}</td></tr>
            <tr><td><b>Conv:</b></td><td>{conversation_id}</td></tr>
            <tr><td><b>Requested:</b></td><td>{activity_requested}</td></tr>
        </table>
        <h3>Customer message:</h3>
        <blockquote>{user_message}</blockquote>
        <p>Reply to this email and your response will be sent back to the customer in chat.</p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = supervisor_email
    msg["X-Escalation-ID"] = escalation_id
    msg["X-Conversation-ID"] = conversation_id
    msg.attach(MIMEText(body, "html"))

    try:
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, supervisor_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Failed to send escalation email: {e}")
        return False


def parse_supervisor_reply(raw):
    lines = raw.split("\n")
    reply = []
    for line in lines:
        if line.startswith(">") or "wrote:" in line or line.strip().startswith("On "):
            break
        reply.append(line)
    return "\n".join(reply).strip()
