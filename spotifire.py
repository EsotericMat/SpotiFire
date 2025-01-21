import os
import time
import logging
from db import MongoDBManager
from ai import generate_playlist
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, ConversationHandler
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv


load_dotenv()
db_manager = MongoDBManager()


def get_auth():
    return SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope="playlist-modify-public",
    )


def get_user_token(user_id):
    """Retrieve a user's Spotify token and refresh if expired."""
    user_data = db_manager.users_collection.find_one({"user_id": f"{user_id}"})
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


# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    try:
        # Generate and send Spotify Auth URL
        auth_url = get_auth().get_authorize_url(state=str(user_id))
        await update.message.reply_text(
            f"Welcome to SpotiFire! Please authenticate with Spotify by clicking this link:\n{auth_url}"
        )
    except Exception as e:
        print(f"Error generating auth URL for user {user_id}: {e}")
        await update.message.reply_text(
            "Something went wrong while generating the Spotify authentication link. Please try again later."
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

    await update.message.reply_text("Please describe the vibe or theme of the playlist you want to create.")
    return GET_PLAYLIST_DESCRIPTION


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Playlist creation canceled.")
    return ConversationHandler.END


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Update {update} caused error {context.error}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Working on it, hold on...')

    message_type = update.message.chat.type
    user_text = update.message.text
    user_id, token = fetch_token_and_userid(update)
    print(f'User {update.message.chat.id} in {message_type}: "{user_text}" ')

    sp = Spotify(auth=token['access_token'])

    songs_objects = generate_playlist(prompt=user_text)
    try:
        songs_ids = generate_playlist_ids(songs_objects, sp)
        user_profile = sp.me()
        new_playlist = sp.user_playlist_create(
            user=user_profile["id"],
            name=user_text,
            public=True
        )
        sp.playlist_add_items(
            # self.current_user['id'],
            playlist_id=new_playlist['id'],
            items=songs_ids,
            position=0
        )
        await update.message.reply_text(f'{user_text} is now on your playlists library, check it out!')

    except Exception as e:
        await update.message.reply_text(f"Can't complete your request right now")
        raise f'Error while creating Spotify playlist: {e}'

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
