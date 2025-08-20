import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

def initiate_call(to_number: str, user_id: str) -> str:
    """Initiates a Twilio call and attaches user_id to webhook."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")
    api_url = os.getenv("API_URL")

    if not all([account_sid, auth_token, from_number, api_url]):
        raise ValueError("Twilio environment variables not set correctly")

    client = Client(account_sid, auth_token)
    call = client.calls.create(
        to=to_number,
        from_=from_number,
        url=f"{api_url}?user_id={user_id}"
    )
    print(f"📞 Call initiated to {to_number}, SID: {call.sid}")
    return call.sid