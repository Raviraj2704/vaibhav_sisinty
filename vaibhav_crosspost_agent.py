import threading
import time
from flask import Flask

app = Flask(__name__)

# This is your 'Agent' logic
def run_agent():
    print("AGENT STARTING: Monitoring loop initiated.")
    while True:
        try:
            print("Checking YouTube for new videos...")
            # [INSERT YOUR YOUTUBE/TWILIO LOGIC HERE]
            
            time.sleep(300) # Wait 5 minutes
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

# Start the agent in the background
threading.Thread(target=run_agent, daemon=True).start()

@app.route('/')
def home():
    return "Agent is running and active!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
