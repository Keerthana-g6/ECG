# backend/alert.py
from twilio.rest import Client
import os

ACCOUNT_SID = os.getenv('TWILIO_SID')
AUTH_TOKEN  = os.getenv('TWILIO_AUTH')
FROM_NUMBER = os.getenv('TWILIO_FROM', 'whatsapp:+14155238886')
TO_NUMBER   = os.getenv('ALERT_TO')

client = None
if ACCOUNT_SID and AUTH_TOKEN:
    client = Client(ACCOUNT_SID, AUTH_TOKEN)

def send_alert(risk):
    if client is None or TO_NUMBER is None:
        raise RuntimeError('Twilio not configured')
    msg = f"⚠ URGENT: High Heart Attack Risk Detected ({risk}%). Immediate action required!"
    client.messages.create(body=msg, from_=FROM_NUMBER, to=TO_NUMBER)