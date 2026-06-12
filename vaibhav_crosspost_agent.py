import os
import time
import threading
import feedparser
from flask import Flask
from twilio.rest import Client

app = Flask(__name__)

# List of channels to monitor
CHANNELS = [
    {"name": "Vaibhav", "id": os.environ.get("CHANNEL_ID_VAIBHAV")},
    {"name": "Cousin", "id": os.environ.get("CHANNEL_ID_COUSIN")}
]

# Tracking dictionary
last_video_ids = {channel["name"]: None for channel in CHANNELS}

def send_whatsapp(channel_name, title, link):
    client = Client(os.environ.get("TWILIO_SID"), os.environ.get("TWILIO_TOKEN"))
    client.messages.create(
        body=f"New video from {channel_name}: {title}\n{link}",
        from_=f"whatsapp:{os.environ.get('TWILIO_NUM')}",
        to=f"whatsapp:{os.environ.get('MY_PHONE_NUMBER')}"
    )

def monitor_youtube():
    while True:
        for channel in CHANNELS:
            url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel['id']}"
            feed = feedparser.parse(url)
            if feed.entries:
                latest = feed.entries[0]
                if last_video_ids[channel["name"]] and latest.id != last_video_ids[channel["name"]]:
                    send_whatsapp(channel["name"], latest.title, latest.link)
                last_video_ids[channel["name"]] = latest.id
        time.sleep(600) # Check every 10 minutes

# Run monitor in background
threading.Thread(target=monitor_youtube, daemon=True).start()

@app.route('/')
def home():
    return "Agent is running!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
