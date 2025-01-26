import os
import time
import logging
import base64
import ai
import urllib.parse
from db import MongoDBManager
from ai import generate_playlist
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, ConversationHandler
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from datetime import datetime
from bot_reactions import BotReactions

load_dotenv()
db_manager = MongoDBManager()
reactor = BotReactions()


def get_auth():
    return SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope="playlist-modify-public playlist-modify-private ugc-image-upload"
    )


def get_user_token(user_id):
    """Retrieve a user's Spotify token and refresh if expired."""
    user_data = db_manager.users_collection.find_one({"user_id": user_id})
    if not user_data:
        print(f"User {user_id} not found in database")
        return None

    token_info = user_data.get("token_info")
    if not token_info:
        print(f"No token found for user {user_id}")
        return None

    expires_at = token_info.get("expires_at")

    if expires_at and expires_at < int(time.time()):
        # Token expired, refresh it
        print(f"Token expired for user {user_id}. Refreshing...")
        sp_oauth = get_auth()
        try:
            new_token_info = sp_oauth.refresh_access_token(token_info["refresh_token"])
            # Update the new token in the database
            db_manager.store_user_token(user_id, new_token_info)
            print("new token info:", new_token_info['access_token'])
            return new_token_info
        except Exception as e:
            print(f"Error refreshing token for user {user_id}: {e}")
            return None
    # Return valid token
    return token_info


def fetch_token_and_userid(update: Update):
    user_id = update.message.from_user.id
    token_info = get_user_token(user_id)

    if not token_info:
        return None, None  # Prompt user to re-authorize

    return user_id, token_info


GET_PLAYLIST_DESCRIPTION = range(1)


def image_to_base64(image_path: str) -> str:
    """Convert an image to Base64-encoded string."""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")


def generate_playlist_ids(songs_object, sp):
    song_ids = []
    for item in songs_object:
        _id = sp.search(
            q=f'track:{item["song"]} artist:{item["artist"]}',
            type='track',
            limit=1
        )
        try:
            song_ids.append(_id['tracks']['items'][0]['id'])
        except Exception:
            print(f'cant find {item["song"]} by {item["artist"]}')

    return song_ids


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command for the bot. Guides the user to authenticate with Spotify."""
    user_id = update.message.from_user.id  # Ensure this is initialized elsewhere in your code
    print("type of user_id:", type(user_id))
    await update.message.reply_text(reactor.craft("greet"))
    # Check if user is already authenticated
    user_token = db_manager.get_user_token(user_id)

    if user_token:
        # Check if the token is expired
        if int(time.time()) > user_token['expires_at']:
            await update.message.reply_text(
                "Your Spotify token has expired. Let me refresh your token"
            )
            _, new_token = fetch_token_and_userid(update)

        await update.message.reply_text("You are already authenticated with Spotify! 🎉 Run /create_playlist to start!.")
        return

    # Prompt user to authenticate if no token is found
    await prompt_user_for_auth(update, user_id)


async def prompt_user_for_auth(update: Update, user_id: int) -> None:
    """Prompts the user to authenticate with Spotify."""
    scope = 'user-read-private playlist-modify-public ugc-image-upload'
    auth_url = (
            f"{os.getenv("SPOTIFY")}/authorize?"
            + urllib.parse.urlencode(
        {
            "client_id": os.getenv("SPOTIPY_CLIENT_ID"),
            "response_type": "code",
            "redirect_uri": os.getenv("SPOTIPY_REDIRECT_URI"),
            "scope": scope,
            "show_dialog": True,
            "state": user_id,
        }
    )
    )

    await update.message.reply_text(
        f"Please authenticate with Spotify by clicking the link below:\n\n{auth_url}\n\n"
        "After authenticating, return here to continue using the bot. 🎧"
    )


async def create_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id, token = fetch_token_and_userid(update)
    message_type = update.message.chat.type
    activity = update.message.text

    print(f'User {update.message.chat.id} in {message_type}: "{activity}" ')

    # Get description
    if not token:
        await update.message.reply_text("You need to authenticate first! Use /start.")
        return ConversationHandler.END

    await update.message.reply_text(reactor.craft("describe"))
    return GET_PLAYLIST_DESCRIPTION


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Playlist creation canceled.")
    return ConversationHandler.END


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Update {update} caused error {context.error}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(reactor.craft("on_it"))

    message_type = update.message.chat.type
    user_text = update.message.text
    user_id, token = fetch_token_and_userid(update)
    print(f'User {update.message.chat.id} in {message_type}: "{user_text}" ')
    sp = Spotify(auth=token['access_token'])
    songs_objects = generate_playlist(prompt=user_text)

    try:
        cover_img_path = ai.generate_image(query=user_text)
        time.sleep(1)
        songs_ids = generate_playlist_ids(songs_objects, sp)
        user_profile = sp.me()
        new_playlist = sp.user_playlist_create(
            user=user_profile["id"],
            name=user_text,
            public=True
        )
        sp.playlist_add_items(
            playlist_id=new_playlist['id'],
            items=songs_ids,
            position=0
        )

        playlist_url = new_playlist['external_urls']['spotify']
        db_manager.add_user_playlist(user_id, user_text)

    except Exception as e:
        await update.message.reply_text(f"Can't complete your request right now")
        print(f'Error while creating Spotify playlist: {e}')
        return ConversationHandler.END

    try:
        cover_base64 = image_to_base64(cover_img_path)
        sp.playlist_upload_cover_image(new_playlist['id'], cover_base64)

    except Exception as e:
        print(f"Error uploading playlist cover image: {e}")

    await update.message.reply_text(f'{reactor.craft('playlist_ready')}\n{playlist_url}')
    return ConversationHandler.END


# Main Function
def main():
    print('SpotiFire is running...')

    # app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()

    playlist_handler = ConversationHandler(
        entry_points=[CommandHandler("create_playlist", create_playlist)],
        states={
            GET_PLAYLIST_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(playlist_handler)

    # Error handler
    app.add_error_handler(error)

    app.run_polling()

    return "OK"


if __name__ == "__main__":
    main()
