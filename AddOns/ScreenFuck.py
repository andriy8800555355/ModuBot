from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import ImageGrab
import io
import os
import json

# Load SUDO users from the file
def load_sudo_users():
    sudo_users_file = "SUDOUsers.json"
    try:
        if os.path.exists(sudo_users_file):
            with open(sudo_users_file, "r", encoding="utf-8") as file:
                return json.load(file)
    except json.JSONDecodeError:
        print(f"Error decoding {sudo_users_file}. Using empty list.")
    except IOError:
        print(f"Error reading {sudo_users_file}. Using empty list.")
    return []

def add_on_commands(app: Client):
    sudo_users = load_sudo_users()

    # Screenshot Command
    @app.on_message(filters.command("screenshot", prefixes=".") & (filters.user(sudo_users) | filters.me))
    async def screenshot_command(client: Client, message: Message):
        try:
            # Capture screenshot
            screenshot = ImageGrab.grab()
            # Save screenshot to BytesIO
            img_bytes = io.BytesIO()
            screenshot.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            # Send screenshot
            await message.reply_photo(photo=img_bytes, caption="Here's your screenshot!")
        except Exception as e:
            await message.reply_text(f"Error capturing screenshot: {e}")

    # Reload SUDO users list
    @app.on_message(filters.command("reloadsudo", prefixes=".") & filters.me)
    async def reload_sudo(client: Client, message: Message):
        nonlocal sudo_users
        sudo_users = load_sudo_users()
        await message.reply_text("SUDO users list reloaded.")