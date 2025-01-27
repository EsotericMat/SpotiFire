import random


class BotReactions:
    GREET = [
        "Hey there, music lover! Let's get connected! 🎵",
        "What's up, music fan? Ready to rock? 🎸",
        "Hello! I'm here to help you find your new favorite jam 🎼",
        "Hey, music enthusiast! Let's get this party started 🎶",
        "Hi there! I'm excited to help you discover new tunes 🎧",
        "Hey, let's get this music party started! 🎵",
    ]

    DESCRIBE = [
        "Describe the vibe you're looking for in your playlist 🎧",
        "Can you describe the vibe for your playlist",
        "Let me know what you are looking for today 🎧",
        "What's on your mind for today's playlist?",
        "What we are looking for today? 🎧",
        "What's the vibe for today?",
        "What do you want to listen to today? 🎧"
    ]

    SOUNDS_GREAT = [
        "Sounds great! 👍",
        "Sounds good! 👍",
        "Sounds like a BANGER! 🤘🏻",
        "Great choice! 👏",
        "You have good taste! 🫵🏼",
        "Winning playlist! 🏆",
        "I'm in love with this idea! 🥰",
        "That going to be a hit! 🔥"
    ]

    ON_IT = [
        "Working on it... Your playlist is coming soon! 💫",
        "Hang tight, I'm creating your playlist as we speak! 🚀",
        "Just a sec, I'm cooking up the perfect playlist for you 👨🏻‍🍳",
        "Almost there... Your playlist is just a few seconds away ✨",
        "I'm on it! Your playlist will be ready in no time ⌛️",
        "Creating your playlist... Please wait 🎵",
        "Just a moment, I'm putting the finishing touches on your playlist 🎧"
    ]

    PLAYLIST_READY = [
        "Your playlist is ready! 🎺 Check it out:",
        "Here's your new playlist 💫: ",
        "Your playlist is ready! 🎧 Let's listen to it:",
        "Your playlist is here! 🔥 Check it out:",
        "Here's your awesome playlist 🤘🏻: ",
    ]

    CONFIG = {
        "greet": GREET,
        "describe": DESCRIBE,
        "sounds_great": SOUNDS_GREAT,
        "on_it": ON_IT,
        "playlist_ready": PLAYLIST_READY
    }

    def craft(self, reaction_type: str):

        if reaction_type not in self.CONFIG:
            raise ValueError(f"Invalid reaction type: {reaction_type}")

        if reaction_type == "on_it":
            return random.choice(self.CONFIG['sounds_great']) + " " + random.choice(self.CONFIG["on_it"])

        return random.choice(self.CONFIG[reaction_type])
