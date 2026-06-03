import os
import threading
import time
import json
import requests
import feedparser
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client

app = Flask(__name__)

# --- CONFIGURATION ---
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_NUM = os.getenv("TWILIO_NUM")
MY_NUM = os.getenv("MY_NUM")

client = Client(TWILIO_SID, TWILIO_AUTH)
STORE_FILE = 'pending_posts.json'
HISTORY_FILE = 'history.txt'

# --- HELPERS ---
def load_pending():
    if not os.path.exists(STORE_FILE): return []
    with open(STORE_FILE, 'r') as f: 
        try: return json.load(f)
        except: return []

def save_pending(data):
    with open(STORE_FILE, 'w') as f: json.dump(data, f, indent=4)

# --- BACKGROUND MONITOR ---
def monitor_loop():
    YOUTUBE_RSS_URL = 'https://www.youtube.com/feeds/videos.xml?channel_id=UCoa5Z3ly38-uX7_P5h8-S1g'
    while True:
        try:
            feed = feedparser.parse(YOUTUBE_RSS_URL)
            if feed.entries:
                latest = feed.entries[0]
                if not os.path.exists(HISTORY_FILE): open(HISTORY_FILE, 'w').close()
                with open(HISTORY_FILE, 'r') as f: history = f.read()

                if latest.id not in history:
                    pending = load_pending()
                    pending.append({'title': latest.title, 'video_url': latest.link})
                    save_pending(pending)
                    with open(HISTORY_FILE, 'a') as f: f.write(latest.id + "\n")
                    
                    client.messages.create(
                        body=f"New video: {latest.title}\nReply YES to post.", 
                        from_=TWILIO_NUM, to=MY_NUM
                    )
        except Exception as e: print(f"Monitor error: {e}")
        time.sleep(300) 

# --- ROUTES ---

# Root route for Render health checks
@app.route('/')
def home():
    return "Bot is active and running", 200

# SMS route for Twilio
@app.route('/sms', methods=['POST'])
def sms_reply():
    msg = request.form.get('Body', '').strip().lower()
    resp = MessagingResponse()
    if msg == 'yes':
        pending = load_pending()
        if pending:
            video = pending.pop(0)
            url = f"https://graph.facebook.com/v21.0/{FB_PAGE_ID}/videos"
            params = {'access_token': FB_PAGE_TOKEN, 'file_url': video['video_url'], 'title': video['title']}
            if requests.post(url, data=params).status_code == 200:
                resp.message(f"Successfully posted: {video['title']}")
                save_pending(pending)
            else: resp.message("Facebook post failed.")
        else: resp.message("No pending videos.")
    return str(resp)

# Start background monitor
threading.Thread(target=monitor_loop, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
