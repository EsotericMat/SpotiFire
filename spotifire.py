import os
from ai import generate_playlist, init_model
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

# global auth
auth = SpotifyOAuth(
                client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
                redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
                scope="playlist-modify-public",
                show_dialog=True
            )


def fetch_token_and_userid(update: Update):
    user_id = update.message.from_user.id
    token = auth.get_access_token(as_dict=False)
    return user_id, token


def generate_playlist_ids(songs_object, sp):
    song_ids = []
    for item in songs_object:
        _id = sp.search(
                q=f'track:{item["song"]} artist:{item["artist"]}',
                type='track',
                limit=1
            )
        if _id:
            song_ids.append(_id['tracks']['items'][0]['id'])

    return song_ids


# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    print('Bot Is Live')

    try:
        # Generate Spotify Auth URL
        await update.message.reply_text(f"Welcome to SpotiFire! Please authenticate with Spotify by clicking this link:\n{auth.get_authorize_url(state=str(user_id))}")

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
        return

    await update.message.reply_text("Please describe the vibe or theme of the playlist you want to create.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Working on it, hold on...')

    message_type = update.message.chat.type
    user_text = update.message.text
    user_id, token = fetch_token_and_userid(update)
    print(f'User {update.message.chat.id} in {message_type}: "{user_text}" ')

    sp = Spotify(auth=token)

    songs_objects = generate_playlist(prompt=user_text)
    try:
        songs_ids = generate_playlist_ids(songs_objects, sp)
        print('Trying to run playlist')
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


# Main Function
def main():
    init_model()

    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("create_playlist", create_playlist))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()
    return "OK"


if __name__ == "__main__":
    main()
