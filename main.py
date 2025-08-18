from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from handlers.twilio_call import initiate_call
from handlers.twilio_ws import twilio_deepgram_bridge
from starlette.websockets import WebSocketState
import uvicorn
import os

app = FastAPI()

@app.get("/api")
def health_check():
    return {"status": "running"}

@app.post("/api/start-call")
async def start_call(request: Request):
    data = await request.json()
    destination_number = data.get("destination_number")
    if not destination_number:
        return {"error": "Missing 'destination_number' in request body"}
    
    sid = initiate_call(destination_number)
    return {"sid": sid}

@app.websocket("/ws")
async def ws_twilio_endpoint(twilio_ws: WebSocket):
    """Endpoint Twilio Media Streams should connect to (use this URL as your websocket target)."""
    await twilio_ws.accept()
    try:
        await twilio_deepgram_bridge(twilio_ws)
    except WebSocketDisconnect:
        print("🔌 Twilio WS disconnected at endpoint.")
    except Exception as e:
        print(f"❌ Unexpected error in endpoint: {e}")
    finally:
        try:
            if twilio_ws.client_state == WebSocketState.CONNECTED:
                await twilio_ws.close()
        except Exception:
            pass

if __name__ == "__main__":
    PORT = int(os.getenv("PORT", 3000))
    ENV = os.getenv("ENV", "dev").lower()  
    reload = False if ENV == "prod" else True
    uvicorn.run("main:app", host="0.0.0.0", port= PORT, reload=reload)