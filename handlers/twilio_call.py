import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

def initiate_call(to_number: str) -> str:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")
    webhook_url = os.getenv("TWILIO_WEBHOOK_URL") 

    if not all([account_sid, auth_token, from_number, webhook_url]):
        raise ValueError("Twilio environment variables not set correctly")

    client = Client(account_sid, auth_token)
    call = client.calls.create(
        to=to_number,
        from_=from_number,
        url=webhook_url
    )
    print(f"📞 Call initiated to {to_number}, SID: {call.sid}")
    return call.sid