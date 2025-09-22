import smtplib, ssl
import os 
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def SendEmail(
    recipientEmails, 
    subject, 
    body, 
    attachments: list = None, 
    cc: list = None, 
    bcc: list = None
    ):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = ", ".join(recipientEmails) if isinstance(recipientEmails, list) else recipientEmails
        msg['Subject'] = subject

        if cc:
            msg['Cc'] = ", ".join(cc)

        msg.attach(MIMEText(body, 'plain'))

        if attachments:
            for file_path in attachments:
                file_path = Path(file_path)
                if file_path.exists():
                    with open(file_path, "rb") as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition', 
                            f'attachment; filename={file_path.name}'
                        )
                        msg.attach(part)

        allRecipients = []
        for recipent in [recipientEmails, cc, bcc]:
            if recipent:
                if isinstance(recipent, list):
                    allRecipients.extend(recipent)
                else:
                    allRecipients.append(recipent)
        
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, allRecipients, msg.as_string())

        print("Email sent successfully")
        
    except Exception as e:
        print(f"Error sending email: {e}")