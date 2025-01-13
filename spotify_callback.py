from flask import Flask, request
from utils import get_auth_manager
from dotenv import load_dotenv
from utils import get_auth_manager
import os


# Load environment variables
load_dotenv()
user_token = ""
app = Flask(__name__)


@app.route("/health")  # Add health check endpoint
def health_check():
    return "OK", 200


# Spotify OAuth Setup
@app.route("/callback")
def spotify_callback():
    code = request.args.get("code")
    user_id = request.args.get("state")  # Telegram user ID passed via 'state'

    if not code or not user_id:
        return "Invalid callback request. Authorization failed.", 400

    try:
        sp_oauth = get_auth_manager(user_id)
        # token_info = sp_oauth.get_access_token(code)
        return "Authorization successful. Token stored.", 200

    except Exception as e:
        return f"Error exchanging token: {str(e)}", 400


if __name__ == "__main__":
    app.run(
        host='0.0.0.0',
        port=int("8080")
    )
