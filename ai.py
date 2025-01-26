import json
import os
import requests
import fal_client
import google.generativeai as ai
from dotenv import load_dotenv

load_dotenv()

def generate_playlist(prompt, n=12):
    """
    Generate a playlist given a prompt.

    This function use the Gemini AI model to generate a playlist given a prompt.
    The AI model is configured with an API key from the `GENAI_API_KEY` environment variable.
    The function takes a prompt and a number of songs to generate as input, and returns a JSON
    array with the chosen songs in the following structure:
    {
        "playlist": [
            {
                "artist": "artist name",
                "song": "song name"
            }
        ]
    }

    :param prompt: The prompt to generate the playlist from
    :param n: The number of songs to generate in the playlist
    :returns: A JSON array with the chosen songs
    """
    sys_prompt = 'You are a pro musician, and you going to create amazing playlists by getting a prompt. You will choose' \
                  'the best songs that fits the prompt, and you will return the chosen songs in a JSON array structure as ' \
                  'following:' \
                  '{artist: artist name, song: song name}. You will also get number of songs to choose for the playlist.' \
                  'The final results suppose to looks like that:' \
                  '{' \
                  'playlist: [' \
                  '     {' \
                  '        "artist": "artist_name",' \
                  '        "song": "song name"' \
                  '      }' \
                  ' ]' \
                  '}'

    user_prompt = f"Create {n*2} songs playlist of: {prompt}"
    ai.configure(api_key=os.getenv("GENAI_API_KEY"))
    model = ai.GenerativeModel(model_name="gemini-1.5-flash",
                               generation_config={'response_mime_type': 'application/json'})
    response = model.generate_content(sys_prompt + "\n" + user_prompt)
    songs = response.text.replace("```json", "").replace('```', '')
    print(songs)
    return json.loads(songs)['playlist']


def generate_image(query):

    prompt = (f"Create a spotify playlist cover picture for a playlist named: {query}, try your best to represent the"
              f"vibes of this playlist and songs")

    handler = fal_client.submit(
        "fal-ai/flux/schnell",
        arguments={
            "prompt": prompt
        },
    )

    result = handler.get()['images'][0]['url']
    response = requests.get(result)
    img_location = f'images/{query.replace(" ","-")}_cover.jpeg'
    # Open a file in write-binary mode and save the content
    with open(img_location, 'wb') as file:
        file.write(response.content)

    return img_location

# def remove_image_from_disk(image_path):
#
#
# if __name__ == '__main__':
#     playlist = "Classic Rock n Roll hits from the 80's"
#     print(generate_playlist(playlist, 4))
