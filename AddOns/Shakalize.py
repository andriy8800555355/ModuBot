import os
import subprocess
from pyrogram import Client, filters
from PIL import Image

def shakalize_image(file_path, intensity):
    with Image.open(file_path) as img:
        quality = max(1, 100 - intensity * 10)
        shakalized_path = f"shakalized_{os.path.basename(file_path)}"
        img.save(shakalized_path, quality=quality)
    return shakalized_path

def shakalize_video(file_path, intensity):
    # Degrade video
    video_bitrate = max(100, 10000 - intensity * 1000)
    audio_bitrate = max(32, 320 - intensity * 32)
    shakalized_path = f"shakalized_{os.path.basename(file_path)}"
    
    command = [
        "ffmpeg",
        "-i", file_path,
        "-b:v", f"{video_bitrate}k",
        "-b:a", f"{audio_bitrate}k",
        "-vf", f"scale=iw/{intensity}:ih/{intensity},scale=iw*{intensity}:ih*{intensity}",
        "-y", shakalized_path
    ]
    subprocess.run(command, check=True)
    return shakalized_path

def epicize_video(file_path):
    video_bitrate = 8
    audio_bitrate = 8
    epicized_path = f"epicized_{os.path.basename(file_path)}"
    
    command = [
        "ffmpeg",
        "-i", file_path,
        "-b:v", f"{video_bitrate}k",
        "-b:a", f"{audio_bitrate}k",
        "-vf", "scale=160:120",
        "-ar", "8000",
        "-y", epicized_path
    ]
    subprocess.run(command, check=True)
    return epicized_path

def add_on_commands(app: Client):
    @app.on_message(filters.command("shakal", prefixes="."))
    def shakal_command(client, message):
        if len(message.command) != 2:
            message.reply_text("Usage: .shakal {1-10}")
            return
        
        try:
            intensity = int(message.command[1])
            if intensity < 1 or intensity > 10:
                raise ValueError
        except ValueError:
            message.reply_text("Please provide a valid intensity level (1-10).")
            return
        
        target_message = message.reply_to_message
        if not target_message:
            message.reply_text("Please reply to a photo or video with the command.")
            return
        
        media = target_message.photo or target_message.video
        if not media:
            message.reply_text("Please reply to a message containing a photo or video.")
            return
        
        file_id = media.file_id
        file_path = client.download_media(file_id)
        
        if target_message.photo:
            processed_file_path = shakalize_image(file_path, intensity)
            client.send_photo(message.chat.id, processed_file_path)
        elif target_message.video:
            processed_file_path = shakalize_video(file_path, intensity)
            client.send_video(message.chat.id, processed_file_path)
        
        os.remove(file_path)
        os.remove(processed_file_path)

    @app.on_message(filters.command("epic", prefixes="."))
    def epic_command(client, message):
        target_message = message.reply_to_message
        if not target_message or not target_message.video:
            message.reply_text("Please reply to a message containing a video.")
            return
        
        file_id = target_message.video.file_id
        file_path = client.download_media(file_id)
        
        processed_file_path = epicize_video(file_path)
        client.send_video(message.chat.id, processed_file_path)
        
        os.remove(file_path)
        os.remove(processed_file_path)

# Note: Do not add client initialization or app.run() here
# It should be done in the main script
