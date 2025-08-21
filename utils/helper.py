import json
from db import users_collection

async def load_config():
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise Exception("❌ config.json not found")
    except json.JSONDecodeError:
        raise Exception("❌ config.json contains invalid JSON")

async def build_prompt(user_id: str) -> str:
    """Builds a custom Deepgram prompt per user based on MongoDB users_collection."""
    user = await users_collection.find_one({"user_id": user_id})
    if not user:
        raise Exception(f"❌ User '{user_id}' not found in DB")

    instruction = user.get("instruction", [])

    base_prompt = (
        "You are Zai, a professional HR assistant for Zinterview.ai.\n\n"
        "Your role is to conduct an initial screening interview.\n\n"
        "Instructions:\n"
        "1. Always begin by politely greeting the candidate.\n"
        "2. Ask only 2 or 3 questions related to the below instruction\n"
    )

    base_prompt += instruction

    base_prompt += (
        "3. Be thorough, professional, and patient while collecting answers.\n"
        "4. Do not provide any additional information beyond what is needed.\n"
        "5. Once all questions are answered:\n"
        "   - Politely thank the candidate.\n"
        "   - Immediately call the function `end_interview` with { \"status\": \"complete\" }.\n\n"
        "Tone & Style:\n"
        "Formal and polite.\n"
        "Clear and concise.\n"
        "No small talk — keep focus strictly on the interview questions."
    )

    return base_prompt


def serialize_user(user: dict) -> dict:
    """Convert Mongo user document into JSON serializable dict."""
    if not user:
        return None
    user["_id"] = str(user["_id"]) 
    return user