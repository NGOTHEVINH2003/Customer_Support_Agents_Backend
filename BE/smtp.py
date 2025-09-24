import smtplib, ssl
import os 
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv


load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

def SendEmail(
    reportType,
    file_stream,
    startDate,
    endDate = None,
    ):
    try:
        msg = MIMEMultipart()
        

        if reportType == "daily":
            subject = f"Daily Report - {startDate.strftime('%Y-%m-%d')}"
        else:
            subject = f"Weekly Report - {startDate.strftime('%Y-%m-%d')} to {endDate.strftime('%Y-%m-%d')}"

        msg['From'] = EMAIL_ADDRESS
        msg['To'] = ADMIN_EMAIL
        msg['Subject'] = subject

        body = MIMEText("Attached is the requested report.", 'plain')
        msg.attach(body)

        part = MIMEBase("application", "octet-stream")
        part.set_payload(file_stream.read())
        encoders.encode_base64(part)
        filename = f"{reportType}_report.xlsx"
        part.add_header("Content-Disposition", f"attachment; filename= {filename}")
        msg.attach(part)

        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, ADMIN_EMAIL, msg.as_string())

        print("Email sent successfully")
        
    except Exception as e:
        print(f"Error sending email: {e}")