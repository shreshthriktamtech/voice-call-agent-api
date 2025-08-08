import os
import websockets
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def sts_connect():
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        raise Exception("DEEPGRAM_API_KEY not found")
    start_time = datetime.utcnow()
    ws  = websockets.connect(
        "wss://agent.deepgram.com/v1/agent/converse",
        subprotocols=["token", api_key]
    )
    end_time = datetime.utcnow()
    print(f"✅ [Deepgram] Connected at {end_time.isoformat()} UTC "
              f"(took {(end_time - start_time).total_seconds():.2f}s)")
    return ws