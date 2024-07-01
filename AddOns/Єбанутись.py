from pyrogram import Client, filters
import os
import random

# Path to the folder containing GIFs
GIF_FOLDER_PATH = "IdI"

TEXT_FILE_PATH = "LULZ.txt"

def add_on_commands(app: Client):
    @app.on_message(filters.command("IdI", prefixes="."))
    def random_gif_command(client, message):
        try:
            gif_files = [f for f in os.listdir(GIF_FOLDER_PATH) if f.endswith('.gif')]
            if gif_files:
                random_gif = random.choice(gif_files)
                gif_path = os.path.join(GIF_FOLDER_PATH, random_gif)
                with open(gif_path, 'rb') as gif_file:
                    client.send_animation(message.chat.id, gif_file)
            else:
                message.reply_text("No GIFs found in the folder.")
        except Exception as e:
            message.reply_text(f"An error occurred: {e}")

    @app.on_message(filters.command("fuck", prefixes="."))
    def random_line_command(client, message):
        try:
            with open(TEXT_FILE_PATH, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                if lines:
                    random_line = random.choice(lines).strip()
                    message.reply_text(random_line)
                else:
                    message.reply_text("The text file is empty.")
        except FileNotFoundError:
            message.reply_text(f"Text file not found: {TEXT_FILE_PATH}")
        except Exception as e:
            message.reply_text(f"An error occurred: {e}")