import uuid
import os
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from typing import Optional
from starlette.websockets import WebSocketState
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
from db import users_collection
from models.user import User

from tasks import call_user_task
from handlers.twilio_ws import twilio_deepgram_bridge
from utils.helper import serialize_user


load_dotenv()

app = FastAPI()
WS_URL = os.getenv("WS_URL")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api")
def health_check():
    return {"status": "running"}

@app.get("/api/users")
async def get_all_users():
    users = []
    cursor = users_collection.find({})
    async for user in cursor:
        users.append(serialize_user(user))
    return users 

@app.post("/api/create-user")
async def create_user(user: User):
    try:
        user_id = str(uuid.uuid4())
        user_dict = user.dict()
        user_dict["user_id"] = user_id

        result = await users_collection.insert_one(user_dict)
        user_dict["_id"] = str(result.inserted_id)

        return JSONResponse(
            status_code=201,
            content={"message": "User created successfully", "user": user_dict}
        )
    except Exception as e:
        # Log the error if needed
        return JSONResponse(
            status_code=500,
            content={"message": "Failed to create user", "error": str(e)}
        )


@app.post("/api/start-batch-call")
async def start_batch_call(request: Request):
    """
    Start a batch of calls.
    Supports:
    - Immediate calls
    - Scheduled calls via `schedule_time` in ISO format
    """
    data = await request.json()
    user_ids = data.get("user_ids", [])
    schedule_time = data.get("schedule_time", "") 
    instruction = data.get("instruction", "")

    for i, uid in enumerate(user_ids):
        if schedule_time:
            from datetime import datetime
            eta = datetime.fromisoformat(schedule_time)
            call_user_task.apply_async(args=[uid], eta=eta)
        else:
            # stagger immediate calls by 15s each
            call_user_task.apply_async(args=[uid], countdown=i*15)

        update_data = {
            "instruction": instruction,
            "schedule_time": schedule_time if schedule_time else None,
        }
        await users_collection.update_one(
            {"user_id": uid},  
            {"$set": update_data}
        )


    return {"status": "queued", "users": user_ids, "scheduled_at": schedule_time}


@app.post("/api/start-call")
async def start_call(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    call_user_task.apply_async(args=[user_id], countdown=1)
    return {"status": "started", "user": user_id}


@app.post("/api/twilio-voice", response_class=PlainTextResponse)
async def twilio_voice(request: Request, user_id: str = None):
    """Twilio webhook that responds with TwiML."""
    user = await users_collection.find_one({"user_id": user_id})
    if not user:
        return "<Response><Say>Sorry, user not found.</Say></Response>"

    name = user["name"]

    result = users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"call_status": "call picked up"}}
    )

    twiml = f"""
    <Response>
        <Say>Hello {name}, we are calling on the behalf of zinterview.ai. Please wait while we connect to our agent</Say>
        <Play>https://procturemeet.s3.ap-southeast-1.amazonaws.com/candidateInfos/33036bc33f78ae15f1e9da525f1b7730df3e7b1d.mp3</Play>
        <Connect>
            <Stream url="{WS_URL}/{user_id}">
                <Parameter name="userId" value="{user_id}" />
            </Stream>
        </Connect>
    </Response>
    """
    return PlainTextResponse(twiml, media_type="application/xml")


@app.post("/api/call-status")
async def call_status(request: Request):
    form_data = await request.form()
    call_status = form_data.get("CallStatus")  # Twilio sends this
    call_sid = form_data.get("CallSid")
    user_id = request.query_params.get("user_id")

    # Update DB
    await users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"call_status": call_status, "call_sid": call_sid}}
    )

    print(f"📡 Status update for {user_id}: {call_status}")
    return {"status": "ok"}



@app.websocket("/ws/{user_id}")
async def ws_twilio_endpoint(twilio_ws: WebSocket, user_id: Optional[str] = None):
    await twilio_ws.accept()

    if user_id:
        print("📞 userId received from path param:", user_id)

    result = users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"call_status": "connected to ai"}}
    )
    try:
        await twilio_deepgram_bridge(twilio_ws, user_id)
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
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=reload)