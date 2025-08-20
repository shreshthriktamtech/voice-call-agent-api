import os
from celery import Celery
from handlers.twilio_call import initiate_call
from db import users_collection
from dotenv import load_dotenv
load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")
celery = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

@celery.task
def call_user_task(user_id: str):
    import asyncio

    async def _call():
        user = await users_collection.find_one({"user_id": user_id})
        if not user:
            return f"user {user_id} not found"
        destination_number = user["destination_number"]
        sid = initiate_call(destination_number, user_id)
        return f"📞 Call started for {user_id}, Twilio SID={sid}"

    return asyncio.run(_call())
