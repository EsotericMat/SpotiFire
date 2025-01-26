from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class MongoDBManager:
    def __init__(self):
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client["SpotifireDB"]
        self.users_collection = self.db["users"]

    def store_user_token(self, user_id: int, token_info: dict):
        """Store or update a user's Spotify token in MongoDB."""
        self.users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"token_info": token_info, "last_update": datetime.now()}},
            upsert=True
        )
        print(f'Insert {user_id} token successfully')

    def get_user_token(self, user_id: int) -> dict:
        """Retrieve a user's Spotify token from MongoDB."""
        user_data = self.users_collection.find_one({"user_id": user_id})
        print(user_data)
        return user_data.get("token_info") if user_data else None

    def delete_user_token(self, user_id: int):
        """Delete a user's Spotify token from MongoDB."""
        self.users_collection.delete_one({"user_id": user_id})

    def add_user_playlist(self, user_id: int, playlist_name: str):
        """Add a playlist name to a user in MongoDB."""
        self.users_collection.update_one(
            {"user_id": user_id},
            {"$set": {f"playlists": {playlist_name: datetime.now()}}}
        )


if __name__ == '__main__':
    MONGO_URI = os.getenv("MONGO_URI")  # Set your MongoDB URI in the .env file
    client = MongoClient(MONGO_URI)

    db = client["SpotifireDB"]
    users_collection = db["users"]

    user = users_collection.find_one({"user_id": 12345})
    print(user['token_info']['refresh_token'])
