from flask import Flask, request
from spotipy import SpotifyOAuth
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
user_token = ""
app = Flask(__name__)


# Spotify OAuth Setup
@app.route("/callback")
def spotify_callback():
    code = request.args.get("code")
    user_id = request.args.get("state")  # Telegram user ID passed via 'state'

    if not code or not user_id:
        return "Invalid callback request. Authorization failed.", 400

    try:
        sp_oauth = SpotifyOAuth(
            client_id=os.getenv("SPOTIPY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
            scope="playlist-modify-public",
            show_dialog=True
        )
        token_info = sp_oauth.get_access_token(code)
        return "Authorization successful. Token stored.", 200

    except Exception as e:
        return f"Error exchanging token: {str(e)}", 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
