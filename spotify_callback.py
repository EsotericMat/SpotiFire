from flask import Flask, request
from spotipy import SpotifyOAuth
from dotenv import load_dotenv
from db import MongoDBManager
import os
import logging
# Load environment variables
load_dotenv()
db_manager = MongoDBManager()
app = Flask(__name__)


def store_callback_token(auth, user_id, code):
    """
    Stores the callback token for a user after successfully receiving it through
    the OAuth process.
    """
    token_info = auth.get_access_token(code=code)  # Fetch the token
    db_manager.store_user_token(user_id, token_info)

@app.route("/health")  # Add health check endpoint
def health_check():
    return "OK", 200

@app.route("/callback")
def spotify_callback():
    code = request.args.get("code")
    user_id = request.args.get("state")  # Telegram user ID passed via 'state'

    if not code or not user_id:
        return "Invalid callback request. Authorization failed.", 400

    try:
        sp_oauth = SpotifyOAuth(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            # redirect_uri=os.getenv("TEST_SPOTIFY_REDIRECT_URI"),
            redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
            scope="user-read-private playlist-modify-public playlist-modify-private ugc-image-upload",
            show_dialog=True
        )
        store_callback_token(sp_oauth, user_id, code)
        return "Authorization successful 👏. Token stored. \nYou can now close this window.", 200

    except Exception as e:
        return f"Error exchanging token: {str(e)}", 400


if __name__ == "__main__":
    app.run(
        host='0.0.0.0',
        port=int("8080"),
        debug=True
    )
