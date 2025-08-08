# 📞 Twilio + Deepgram Realtime Interview Bot

This project connects **Twilio** voice calls with **Deepgram's Realtime API** using **FastAPI WebSockets**.  
It allows a bot to speak, listen, transcribe in real-time, detect interruptions, and gracefully end the call.

---

## 🚀 Features
- Make a **real phone call** using Twilio.
- Stream **real-time audio** from Twilio to Deepgram.
- Transcribe conversation in real-time with **Deepgram Agent API**.
- Detect **barge-in** (user starts speaking) and handle gracefully.
- Log **full conversation transcript** when call ends.
- Health check endpoint for monitoring.

---

## 🛠 Requirements

- **Python 3.9+**
- **requirements.txt** already included in the repo.

Install dependencies:

```bash
pip install -r requirements.txt
