from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import ImageGrab
import io

def add_on_commands(app: Client):
    # Screenshot Command
    @app.on_message(filters.command("screenshot", prefixes=".") & filters.me)
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