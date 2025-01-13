import os
from ai import generate_playlist
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, ConversationHandler
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import logging

load_dotenv()

# global auth
auth = SpotifyOAuth(
                client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
                redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
                scope="playlist-modify-public",
                show_dialog=True,
                cache_path=".cache"
            )

GET_PLAYLIST_DESCRIPTION = range(1)


def fetch_token_and_userid(update: Update):
    user_id = update.message.from_user.id
    token = auth.get_access_token()
    print(f"Token info for user {user_id}: {token}")
    return user_id, token

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

        except:
            print(f'cant find {item["song"]} by {item["artist"]}')

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
    try:
        print('Creating playlist')
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

    except Exception as e:
        print(f"Error in create_playlist: {str(e)}")
        await update.message.reply_text("Something went wrong. Please try authenticating again with /start")
        return ConversationHandler.END



async def handle_playlist_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get the description from the user
    description = update.message.text
    user_id, token = fetch_token_and_userid(update)

    # Generate or create the playlist with the given description
    # (This is where you'd integrate with your playlist creation logic)
    playlist_name = f"Playlist based on: {description}"
    await update.message.reply_text(f"Your playlist '{playlist_name}' has been created!")

    # End the conversation
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Playlist creation canceled.")
    return ConversationHandler.END


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Update {update} caused error {context.error}")


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

    return ConversationHandler.END


# Main Function
def main():
    print('On it')

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
