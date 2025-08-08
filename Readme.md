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
- **requirements.txt** included in the repo.

---

## ⚙️ Environment Variables

You need to set the following environment variables (for example, in a `.env` file):

```env
DEEPGRAM_API_KEY=your_deepgram_api_key_here
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_number_here
PORT=3000
TWILIO_WEBHOOK_URL=https://your-server.com/ws
