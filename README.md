# Discord Music Bot

A simple Discord bot that can play music from YouTube in voice channels.

## Prerequisites

- Python 3.8 or higher
- FFmpeg installed on your system
- Discord Bot Token
- Discord.py library and other dependencies

## Setup

1. Install FFmpeg on your system:
   - Windows: Download from https://ffmpeg.org/download.html
   - Linux: `sudo apt-get install ffmpeg`
   - macOS: `brew install ffmpeg`

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root and add your Discord bot token:
   ```
   DISCORD_TOKEN=your_bot_token_here
   OPENAI_TOKEN=your_token_here
   ```

4. Run the bot:
   ```bash
   python bot.py
   ```

## Commands

- `!join` - Bot joins your current voice channel
- `!leave` - Bot leaves the voice channel
- `!play [url]` - Plays audio from a YouTube URL
- `!pause` - Pauses the current song
- `!resume` - Resumes playing the current song
- `!stop` - Stops playing and clears the queue

## Note

Make sure to replace `your_bot_token_here` in the `.env` file with your actual Discord bot token. 
