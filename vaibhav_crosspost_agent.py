import os
import time
import threading
import traceback

import feedparser
from flask import Flask
from twilio.rest import Client

app = Flask(__name__)

# Environment variables
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
MY_PHONE_NUMBER = os.getenv("MY_PHONE_NUMBER")

# Twilio WhatsApp Sandbox number
TWILIO_NUM = "whatsapp:+14155238886"

# Vaibhav Sisinty YouTube Channel ID
CHANNEL_ID = "UClXAalunTPaX1YV185DWUeg"
YOUTUBE_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"

CHECK_INTERVAL_SECONDS = 300


def send_whatsapp(message):
    try:
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not MY_PHONE_NUMBER:
            print("Twilio environment variables are missing")
            return

        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        client.messages.create(
            body=message,
            from_=TWILIO_NUM,
            to=f"whatsapp:{MY_PHONE_NUMBER}",
        )

        print("WhatsApp message sent successfully")

    except Exception as e:
        print(f"Twilio Error: {e}")
        traceback.print_exc()


def run_agent():
    print("Agent Started")

    send_whatsapp("Vaibhav Crosspost Agent Started Successfully")

    last_video_id = None

    while True:
        try:
            print("Checking YouTube feed...")

            feed = feedparser.parse(YOUTUBE_URL)

            if not feed.entries:
                print("No feed entries found")
                time.sleep(CHECK_INTERVAL_SECONDS)
                continue

            latest_video = feed.entries[0]
            latest_video_id = latest_video.id

            if last_video_id is None:
                last_video_id = latest_video_id
                print(f"Tracking: {latest_video.title}")

            elif latest_video_id != last_video_id:
                title = latest_video.title
                link = latest_video.link

                send_whatsapp(
                    f"New Vaibhav Sisinty Video\n\n"
                    f"Title: {title}\n\n"
                    f"Watch Here:\n{link}"
                )

                last_video_id = latest_video_id

                print(f"New Video Detected: {title}")

        except Exception as e:
            print(f"Feed Error: {e}")
            traceback.print_exc()

        time.sleep(CHECK_INTERVAL_SECONDS)


threading.Thread(
    target=run_agent,
    daemon=True,
).start()


@app.route("/")
def home():
    return "Vaibhav Crosspost Agent Running"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port,
    )
