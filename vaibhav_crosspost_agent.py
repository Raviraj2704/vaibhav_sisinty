import threading
import time
import os
import feedparser
from flask import Flask
from twilio.rest import Client

app = Flask(__name__)

# --- CONFIGURATION (Use Render Environment Variables) ---
TWILIO_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_NUMBER = 'whatsapp:+14155238886' # Your Twilio number
MY_NUMBER = os.environ.get('MY_PHONE_NUMBER')
YOUTUBE_URL = 'https://www.youtube.com/feeds/videos.xml?channel_id=YOUR_CHANNEL_ID'

def send_whatsapp(message):
    client = Client(TWILIO_SID, TWILIO_TOKEN)
    client.messages.create(body=message, from_=TWILIO_NUMBER, to=f'whatsapp:{MY_NUMBER}')

def run_agent():
    print("AGENT STARTING: Monitoring loop initialized.")
    last_video_id = None
    
    while True:
        try:
            print("Checking YouTube for new videos...")
            feed = feedparser.parse(YOUTUBE_URL)
            
            if feed.entries:
                latest_video = feed.entries[0]
                if latest_video.id != last_video_id:
                    print(f"New video found: {latest_video.title}")
                    send_whatsapp(f"New Video: {latest_video.title}\n{latest_video.link}")
                    last_video_id = latest_video.id
            
        except Exception as e:
            print(f"Error in monitoring loop: {e}")
        
        # Wait 5 minutes
        time.sleep(300)

# --- START BACKGROUND WORKER ---
# This runs your YouTube check without stopping the Web Server
threading.Thread(target=run_agent, daemon=True).start()

# --- WEB SERVER (For UptimeRobot) ---
@app.route('/')
def home():
    return "Agent is running and active!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
