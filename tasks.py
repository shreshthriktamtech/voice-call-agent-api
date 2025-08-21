# tasks.py
import os
from celery import Celery
from pymongo import MongoClient
from handlers.twilio_call import initiate_call
from dotenv import load_dotenv

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL")
MONGO_URL = os.getenv("MONGO_URI")

# Celery setup
celery = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)

# Synchronous MongoDB client
mongo_client = MongoClient(MONGO_URL)
db = mongo_client["voice-agent-api"] 
users_collection = db["users"]

@celery.task
def call_user_task(user_id: str):
    print(users_collection)
    # Update status to 'calling' before starting
    result = users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"call_status": "initiated"}}
    )
    
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        return f"user {user_id} not found"

    phone = user["phone"]
    sid = initiate_call(phone, user_id)

    # Save Twilio SID for tracking
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"twilio_sid": sid}}
    )

    return f"📞 Call started for {user_id}, Twilio SID={sid}"
