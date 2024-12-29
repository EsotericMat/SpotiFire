import json
import torch
from dotenv import load_dotenv
from transformers import pipeline

load_dotenv()


def init_model():
    global pipe
    pipe = pipeline(
        "text-generation",
        model="google/gemma-2-2b-it",
        model_kwargs={"torch_dtype": torch.bfloat16},
        device="mps",  # replace with "mps" to run on a Mac device
    )

def generate_playlist(prompt, n=12):

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

    messages = [
        {"role": "user", "content": sys_prompt + "\n" + user_prompt},
    ]
    outputs = pipe(messages, max_new_tokens=1000)
    response = outputs[0]["generated_text"][-1]["content"].replace("```json", "").replace('```', '')
    print(response)
    return json.loads(response)['playlist']


if __name__ == '__main__':
    playlist = "Classic Country hits from the 80's "
    print(generate_playlist(playlist, 4))
