import imaplib
import os
from dotenv import load_dotenv

load_dotenv()
email_addr = os.getenv("WORKDAY_EMAIL_ADDRESS")
app_password = os.getenv("WORKDAY_EMAIL_APP_PASSWORD")

try:
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(email_addr, app_password)
    print("IMAP Login successful!")
except Exception as e:
    print(f"IMAP Login failed: {e}")
