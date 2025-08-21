import asyncio
import base64
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
from starlette.websockets import WebSocketState
from handlers.deepgram_ws import sts_connect
from utils.helper import load_config, build_prompt
from db import users_collection
load_dotenv()

async def clear_twilio_stream_on_barge_in(decoded, twilio_ws, streamsid):
    """Handle barge-in detection and clear Twilio stream."""
    try:
        if decoded.get("type") == "UserStartedSpeaking":
            clear_message = {
                "event": "clear",
                "streamSid": streamsid
            }
            await twilio_ws.send_text(json.dumps(clear_message))
    except Exception as e:
        print(f"❌ clear_twilio_stream_on_barge_in error: {e}")


async def finalize_interview(twilio_ws, conversation_log, user_id=None):
    """End the interview and log the transcript."""
    try:
        print("✅ Interview completed. Final transcript:")
        for turn in conversation_log:
            print(f"[{turn['role']}] {turn['content']}")

        # Give Deepgram time to finish sending final messages
        await asyncio.sleep(2)

        if twilio_ws.client_state == WebSocketState.CONNECTED:
            await twilio_ws.close()
            print("🔌 Twilio WebSocket closed cleanly.")
        else:
            print("⚠️ Twilio WebSocket already closed.")

        # Update call status in DB
        if user_id:
            users_collection.update_one(
                {"user_id": user_id},
                {"$set": {
                    "call_status": "completed",
                    "transcription": conversation_log  # save transcript
                }}
            )


    except Exception as e:
        print(f"❌ finalize_interview error: {e}")



async def process_deepgram_text(decoded, twilio_ws, sts_ws, streamsid, conversation_log, user_id = None):
    """Process incoming text messages from Deepgram and handle interview flow."""
    print(decoded)
    try:
        if decoded["type"] == "ConversationText":
            conversation_log.append({
                "role": decoded["role"],
                "content": decoded["content"]
            })

            if decoded["content"].lower().strip().endswith("goodbye.") or \
               "interview is complete" in decoded["content"].lower():
                await finalize_interview(twilio_ws, conversation_log)
                return

        elif decoded["type"] == "FunctionCallRequest":
            for fn in decoded.get("functions", []):
                if fn.get("name") == "end_interview":
                    await finalize_interview(twilio_ws, conversation_log, user_id)
                    return

        await clear_twilio_stream_on_barge_in(decoded, twilio_ws, streamsid)
    except Exception as e:
        print(f"❌ process_deepgram_text error: {e}")


async def forward_audio_to_deepgram(sts_ws, audio_queue):
    """Send audio chunks to Deepgram."""
    try:
        while True:
            chunk = await audio_queue.get()
            await sts_ws.send(chunk)
    except Exception as e:
        print(f"❌ forward_audio_to_deepgram error: {e}")


async def relay_deepgram_to_twilio(sts_ws, twilio_ws, streamsid_queue, conversation_log, user_id = None):
    """Receive Deepgram responses and relay them to Twilio."""
    try:
        streamsid = await streamsid_queue.get()

        async for message in sts_ws:
            if isinstance(message, str):
                decoded = json.loads(message)
                await process_deepgram_text(decoded, twilio_ws, sts_ws, streamsid, conversation_log, user_id)
            else:
                # Send Deepgram audio directly
                raw_mulaw = message
                media_message = {
                    "event": "media",
                    "streamSid": streamsid,
                    "media": {"payload": base64.b64encode(raw_mulaw).decode("ascii")}
                }

                if twilio_ws.client_state == WebSocketState.CONNECTED:
                    await twilio_ws.send_text(json.dumps(media_message))
                else:
                    break
    except Exception as e:
        print(f"❌ relay_deepgram_to_twilio outer error: {e}")


async def receive_twilio_audio(twilio_ws: WebSocket, audio_queue, streamsid_queue):
    """Receive audio from Twilio and push it to the processing queue."""
    BUFFER_SIZE = 20 * 160
    inbuffer = bytearray()

    try:
        while True:
            try:
                message = await twilio_ws.receive_text()
                data = json.loads(message)
                event = data.get("event")

                if event == "start":
                    streamsid = data["start"]["streamSid"]
                    streamsid_queue.put_nowait(streamsid)

                elif event == "media":
                    if data["media"]["track"] == "inbound":
                        chunk = base64.b64decode(data["media"]["payload"])
                        inbuffer.extend(chunk)

                elif event == "stop":
                    break

                while len(inbuffer) >= BUFFER_SIZE:
                    chunk = inbuffer[:BUFFER_SIZE]
                    audio_queue.put_nowait(chunk)
                    inbuffer = inbuffer[BUFFER_SIZE:]

            except Exception as msg_e:
                print(f"⚠️ Error parsing Twilio message: {msg_e}")
                break
    except WebSocketDisconnect:
        print("🔌 WebSocket disconnected")
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"call_status": "disconnected"}}
        )
    except Exception as e:
        print(f"❌ receive_twilio_audio error: {e}")


async def twilio_deepgram_bridge(twilio_ws: WebSocket, user_id):
    """Main handler to bridge Twilio and Deepgram."""
    conversation_log = []
    audio_queue = asyncio.Queue()
    streamsid_queue = asyncio.Queue()

    if user_id:
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {
                "call_status": "talking",
            }}
        )

    try:
        async with sts_connect() as sts_ws:
            config_message = await load_config()
            config_message["agent"]["think"]["prompt"] = await build_prompt(user_id)
            await sts_ws.send(json.dumps(config_message))

            tasks = [
                asyncio.create_task(forward_audio_to_deepgram(sts_ws, audio_queue)),
                asyncio.create_task(relay_deepgram_to_twilio(sts_ws, twilio_ws, streamsid_queue, conversation_log, user_id)),
                asyncio.create_task(receive_twilio_audio(twilio_ws, audio_queue, streamsid_queue))
            ]

            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in tasks:
                task.cancel()
    except Exception as e:
        print(f"❌ Error in twilio_deepgram_bridge: {e}")

