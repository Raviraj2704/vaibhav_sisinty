import json
import os
import threading
import time
import traceback
import feedparser
import requests
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# --- CONFIGURATION ---
# Define your channels here
CHANNELS = [
    {"name": "Vaibhav", "id": os.getenv("CHANNEL_ID_VAIBHAV", "UClXAalunTPaX1YV185DWUeg")},
    {"name": "Cousin", "id": os.getenv("CHANNEL_ID_COUSIN")} # Ensure this is in your env vars
]

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
MY_PHONE_NUMBER = os.getenv("MY_PHONE_NUMBER")
TWILIO_NUM = os.getenv("TWILIO_NUM", "whatsapp:+14155238886").lower()

# Facebook Config (applies to all channels in this setup)
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
GRAPH_API_VERSION = os.getenv("GRAPH_API_VERSION", "v20.0")

STATE_FILE = "agent_state.json"
state_lock = threading.Lock()

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"channels": {ch["name"]: {"last_video_id": None} for ch in CHANNELS}, "pending_video": None}
    with open(STATE_FILE, "r") as f: return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f: json.dump(state, f, indent=2)

def send_whatsapp(message):
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(body=message, from_=TWILIO_NUM, to=f"whatsapp:{MY_PHONE_NUMBER}")
    except Exception as e: print(f"Twilio Error: {e}")

def run_agent():
    print("Multi-Channel Agent Started", flush=True)
    while True:
        for channel in CHANNELS:
            try:
                url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel['id']}"
                feed = feedparser.parse(url)
                if not feed.entries: continue
                
                latest = feed.entries[0]
                video_id = latest.get("yt_videoid") or latest.get("id")
                
                with state_lock:
                    state = load_state()
                    # Initialize channel state if missing
                    if "channels" not in state: state["channels"] = {}
                    if channel["name"] not in state["channels"]: state["channels"][channel["name"]] = {"last_video_id": None}
                    
                    last_id = state["channels"][channel["name"]]["last_video_id"]
                    
                    if last_id is None:
                        state["channels"][channel["name"]]["last_video_id"] = video_id
                        save_state(state)
                    elif video_id != last_id:
                        # New video detected!
                        state["channels"][channel["name"]]["last_video_id"] = video_id
                        state["pending_video"] = {"title": latest.title, "link": latest.link, "channel": channel["name"]}
                        save_state(state)
                        send_whatsapp(f"New video from {channel['name']}: {latest.title}\n\nReply POST to publish to FB.")
            except Exception as e: print(f"Error checking {channel['name']}: {e}")
        time.sleep(300)

@app.route("/twilio/whatsapp", methods=["POST"])
def twilio_whatsapp_reply():
    body = request.form.get("Body", "").strip().upper()
    with state_lock:
        state = load_state()
        pending = state.get("pending_video")
        if body == "POST" and pending:
            # Post to Facebook logic
            # (Insert your post_to_facebook(pending) logic here)
            state["pending_video"] = None
            save_state(state)
            send_whatsapp("Posted to Facebook!")
        elif body == "CANCEL":
            state["pending_video"] = None
            save_state(state)
            send_whatsapp("Cancelled.")
    return str(MessagingResponse())

threading.Thread(target=run_agent, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
