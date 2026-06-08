import json
import os
import threading
import time
import traceback
from datetime import datetime, timezone

import feedparser
import requests
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
MY_PHONE_NUMBER = os.getenv("MY_PHONE_NUMBER")
TWILIO_NUM = os.getenv("TWILIO_NUM", "whatsapp:+14155238886")

FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
GRAPH_API_VERSION = os.getenv("GRAPH_API_VERSION", "v25.0")

CHANNEL_ID = os.getenv("CHANNEL_ID", "UClXAalunTPaX1YV185DWUeg")
YOUTUBE_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"

CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "300"))
STATE_FILE = os.getenv("STATE_FILE", "agent_state.json")

state_lock = threading.Lock()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_state():
    if not os.path.exists(STATE_FILE):
        return {
            "last_video_id": None,
            "pending_video": None,
            "last_facebook_post_id": None,
        }

    with open(STATE_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(state, file, indent=2)


def send_whatsapp(message):
    try:
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not MY_PHONE_NUMBER:
            print("Missing Twilio environment variables")
            return

        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        client.messages.create(
            body=message,
            from_=TWILIO_NUM,
            to=f"whatsapp:{MY_PHONE_NUMBER}",
        )

        print("WhatsApp message sent")

    except Exception as e:
        print(f"Twilio Error: {e}")
        traceback.print_exc()


def get_latest_video():
    feed = feedparser.parse(YOUTUBE_URL)

    if not feed.entries:
        return None

    latest = feed.entries[0]

    return {
        "id": latest.get("yt_videoid") or latest.get("id") or latest.get("link"),
        "title": latest.get("title", "New YouTube Video"),
        "link": latest.get("link"),
        "published": latest.get("published", ""),
        "detected_at": now_iso(),
    }


def send_approval_request(video):
    message = (
        "New Vaibhav Sisinty video detected.\n\n"
        f"Title: {video['title']}\n\n"
        f"Watch: {video['link']}\n\n"
        "Reply POST to publish this on Facebook.\n"
        "Reply CANCEL to skip."
    )

    send_whatsapp(message)


def post_to_facebook(video):
    if not FACEBOOK_PAGE_ID or not FACEBOOK_PAGE_ACCESS_TOKEN:
        raise RuntimeError("Missing FACEBOOK_PAGE_ID or FACEBOOK_PAGE_ACCESS_TOKEN")

    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{FACEBOOK_PAGE_ID}/feed"

    message = (
        "New video from Vaibhav Sisinty\n\n"
        f"{video['title']}\n\n"
        f"{video['link']}"
    )

    response = requests.post(
        url,
        data={
            "message": message,
            "link": video["link"],
            "access_token": FACEBOOK_PAGE_ACCESS_TOKEN,
        },
        timeout=30,
    )

    data = response.json()

    if response.status_code >= 400 or "error" in data:
        raise RuntimeError(data.get("error", data))

    return data


def run_agent():
    print("Agent Started")

    send_whatsapp(
        "Vaibhav Crosspost Agent Started. I will ask before posting to Facebook."
    )

    while True:
        try:
            print("Checking YouTube feed...")

            latest_video = get_latest_video()

            if latest_video is None:
                print("No feed entries found")
                time.sleep(CHECK_INTERVAL_SECONDS)
                continue

            with state_lock:
                state = load_state()
                last_video_id = state.get("last_video_id")

                if last_video_id is None:
                    state["last_video_id"] = latest_video["id"]
                    save_state(state)
                    print(f"Tracking current video: {latest_video['title']}")

                elif latest_video["id"] != last_video_id:
                    state["last_video_id"] = latest_video["id"]
                    state["pending_video"] = latest_video
                    save_state(state)

                    print(f"New video detected: {latest_video['title']}")
                    send_approval_request(latest_video)

        except Exception as e:
            print(f"Feed Error: {e}")
            traceback.print_exc()

        time.sleep(CHECK_INTERVAL_SECONDS)


@app.route("/")
def home():
    return "Vaibhav Crosspost Agent Running"


@app.route("/twilio/whatsapp", methods=["POST"])
def twilio_whatsapp_reply():
    incoming_from = request.form.get("From", "")
    body = request.form.get("Body", "").strip().upper()

    expected_from = f"whatsapp:{MY_PHONE_NUMBER}"

    resp = MessagingResponse()

    if incoming_from != expected_from:
        print(f"Ignoring message from unauthorized number: {incoming_from}")
        return str(resp)

    try:
        with state_lock:
            state = load_state()
            pending_video = state.get("pending_video")

            if body in ["POST", "APPROVE", "YES"]:
                if not pending_video:
                    send_whatsapp("No pending video is waiting for Facebook approval.")
                    return str(resp)

                facebook_result = post_to_facebook(pending_video)
                facebook_post_id = facebook_result.get("id")

                state["last_facebook_post_id"] = facebook_post_id
                state["pending_video"] = None
                save_state(state)

                send_whatsapp(
                    "Approved and posted to Facebook successfully.\n\n"
                    f"Facebook Post ID: {facebook_post_id}"
                )

            elif body in ["CANCEL", "SKIP", "NO"]:
                if pending_video:
                    skipped_title = pending_video["title"]
                    state["pending_video"] = None
                    save_state(state)

                    send_whatsapp(
                        "Facebook posting cancelled.\n\n"
                        f"Skipped: {skipped_title}"
                    )
                else:
                    send_whatsapp("No pending video to cancel.")

            else:
                send_whatsapp(
                    "Reply POST to approve the latest video for Facebook, "
                    "or CANCEL to skip."
                )

    except Exception as e:
        print(f"Approval/Facebook Error: {e}")
        traceback.print_exc()
        send_whatsapp(f"Facebook posting failed: {e}")

    return str(resp)


threading.Thread(
    target=run_agent,
    daemon=True,
).start()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
