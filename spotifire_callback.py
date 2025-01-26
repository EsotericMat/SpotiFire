import os
import urllib.parse
from http.client import responses
from flask import Flask, redirect, request, jsonify
from dotenv import load_dotenv
import requests
from datetime import datetime
from db import MongoDBManager

load_dotenv()
app = Flask(__name__)

SPOTIFY = "https://accounts.spotify.com"
AUTH_URL = f"{SPOTIFY}/authorize"
TOKEN_URL = f"{SPOTIFY}/api/token"
API_URL = f"https://api.spotify.com/v1"
SESSION = {}
mongo = MongoDBManager()


def store_callback_token(user_id, token_info):
    mongo.store_user_token(user_id, token_info)

@app.route("/")
def index():
    return "Welcome \n<a href='/login'> Login to Spotify </a>"


# @app.route("/login")
# def login():
#     scope = 'playlist-modify-public'
#     params = {
#         "client_id": os.getenv("SPOTIPY_CLIENT_ID"),
#         "redirect_uri": os.getenv("SPOTIPY_REDIRECT_URI"),
#         "scope": scope,
#         "response_type": "code",
#         "show_dialog": True
#     }
#     auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
#     return redirect(auth_url)


@app.route("/callback")
def callback():
    return "Authorization successful. Token stored. \nYou can now close this window.", 200


@app.route("/login")
def login():
    print("----- I'm using this method ----")
    user_id = int(request.args.get("state"))
    user_token = mongo.get_user_token(user_id)
    # Check token expire time
    if user_token:
        if datetime.now().timestamp() > user_token['expires_in']:
            return redirect("/refresh_token")

        return "Authorization successful", 200

    else:
        if 'error' in request.args:
            return jsonify({'error': request.args['error']})

        if 'code' in request.args:
            req_body = {
                "code": request.args['code'],
                "grant_type": "authorization_code",
                "redirect_uri": os.getenv("SPOTIPY_REDIRECT_URI"),
                "client_id": os.getenv("SPOTIPY_CLIENT_ID"),
                "client_secret": os.getenv("SPOTIPY_CLIENT_SECRET"),
                "scope": "playlist-modify-public playlist-modify-private ugc-image-upload"
            }
            response = requests.post(TOKEN_URL, data=req_body)
            token_info = response.json()
            store_callback_token(user_id, token_info)
            return "Authorization successful. Token stored. \nYou can now close this window.", 200


@app.route("/refresh_token")
def refresh_token():
    print("---- Need to refresh the token ----")
    user_id = request.args.get("state")
    if 'refresh_token' not in SESSION:
        return redirect("/login")

    if datetime.now().timestamp() > SESSION['expires_in']:
        req_body = {
            "grant_type": "refresh_token",
            "refresh_token": SESSION["refresh_token"],
            "client_id": os.getenv("SPOTIPY_CLIENT_ID"),
            "client_secret": os.getenv("SPOTIPY_CLIENT_SECRET"),
            "scope": "playlist-modify-public playlist-modify-private ugc-image-upload"
        }
        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()
        store_callback_token(user_id, new_token_info)
        return "Refreshed.. New Token Stored! You can close this window now"
    else:
        return "Token is up to date"


if __name__ == "__main__":
    app.run(
        host='localhost',
        port=8080,
        debug=True
    )
