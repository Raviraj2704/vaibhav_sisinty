import os
import time
import threading
import traceback
import feedparser
from flask import Flask
from twilio.rest import Client

app = Flask(name)

==================================
ENVIRONMENT VARIABLES
==================================

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
MY_PHONE_NUMBER = os.getenv("MY_PHONE_NUMBER")

Twilio Sandbox Number

TWILIO_NUM = "whatsapp:+14155238886"

Vaibhav Sisinty Channel ID

CHANNEL_ID = "UClXAalunTPaX1YV185DWUeg"

YOUTUBE_URL = (
f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
)

==================================
SEND WHATSAPP MESSAGE
==================================

def send_whatsapp(message):
try:
client = Client(
TWILIO_ACCOUNT_SID,
TWILIO_AUTH_TOKEN
)

    client.messages.create(
        body=message,
        from_=TWILIO_NUM,
        to=f"whatsapp:{MY_PHONE_NUMBER}"
    )

    print("WhatsApp message sent successfully")

except Exception as e:
    print(f"Twilio Error: {e}")
    traceback.print_exc()
==================================
YOUTUBE MONITOR
==================================

def run_agent():
print("Agent Started")

# Test message on startup
send_whatsapp(
    "✅ Vaibhav Crosspost Agent Started Successfully"
)

last_video_id = None

while True:
    try:
        print("Checking YouTube feed...")

        feed = feedparser.parse(YOUTUBE_URL)

        if feed.entries:

            latest_video = feed.entries[0]

            if last_video_id is None:
                last_video_id = latest_video.id
                print(
                    f"Tracking: {latest_video.title}"
                )

            elif latest_video.id != last_video_id:

                title = latest_video.title
                link = latest_video.link

                send_whatsapp(
                    f"🎥 New Vaibhav Sisinty Video\n\n"
                    f"Title: {title}\n\n"
                    f"Watch Here:\n{link}"
                )

                last_video_id = latest_video.id

                print(
                    f"New Video Detected: {title}"
                )

        else:
            print("No feed entries found")

    except Exception as e:
        print(f"Feed Error: {e}")
        traceback.print_exc()

    # Check every 5 minutes
    time.sleep(300)
==================================
START BACKGROUND THREAD
==================================

threading.Thread(
target=run_agent,
daemon=True
).start()

==================================
HEALTH CHECK
==================================

@app.route("/")
def home():
return "Vaibhav Crosspost Agent Running"

==================================
START APP
==================================

if name == "main":
port = int(os.environ.get("PORT", 10000))

app.run(
    host="0.0.0.0",
    port=port
)
