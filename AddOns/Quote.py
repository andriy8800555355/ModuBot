from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from pyrogram import Client, filters
import textwrap

# Function to generate quote image
def generate_quote_image(quote_text, user_name, user_photo):
    # Create a blank image with transparent background
    base = Image.new('RGBA', (600, 400), (0, 0, 0, 0))
    
    # Load Comic Sans MS font
    font_path = "Comic Sans MS.ttf"
    font = ImageFont.truetype(font_path, size=30)
    small_font = ImageFont.truetype(font_path, size=20)
    
    # Draw text on the image
    draw = ImageDraw.Draw(base)
    
    # Wrap text to fit within the image width
    wrapped_text = textwrap.fill(quote_text, width=40)
    
    # Calculate text size and position
    text_bbox = draw.textbbox((0, 0), wrapped_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (600 - text_width) / 2
    text_y = (400 - text_height) / 2
    
    # Fill the text area with white color with some transparency
    draw.rectangle([text_x - 10, text_y - 10, text_x + text_width + 10, text_y + text_height + 10], fill=(255, 255, 255, 230))
    
    # Draw the text on the image
    draw.text((text_x, text_y), wrapped_text, font=font, fill='black')
    
    # Add user's name at the bottom
    name_text = f"- {user_name}"
    name_bbox = draw.textbbox((0, 0), name_text, font=small_font)
    name_width = name_bbox[2] - name_bbox[0]
    name_height = name_bbox[3] - name_bbox[1]
    draw.text((600 - name_width - 10, 400 - name_height - 10), name_text, font=small_font, fill='black')
    
    # Add user's profile picture at the top left
    if user_photo:
        profile_pic = Image.open(BytesIO(user_photo)).convert("RGBA")
        profile_pic = profile_pic.resize((50, 50), Image.LANCZOS)
        base.paste(profile_pic, (10, 10), profile_pic)
    
    # Add border around the text area to give it a sticker-like appearance
    border_margin = 5
    draw.rectangle(
        [text_x - 10 - border_margin, text_y - 10 - border_margin, text_x + text_width + 10 + border_margin, text_y + text_height + 10 + border_margin], 
        outline='black', width=2
    )
    
    # Save image to BytesIO buffer in WebP format
    image_stream = BytesIO()
    base.save(image_stream, format='WEBP')
    image_stream.name = "sticker.webp"  # Assign a name to the BytesIO object
    image_stream.seek(0)
    
    return image_stream

# Function to handle command
def add_on_commands(app: Client):
    @app.on_message(filters.command("quotly", prefixes="."))
    def quotly_command(client, message):
        if message.reply_to_message:
            quote_text = message.reply_to_message.text or message.reply_to_message.caption
            user_name = message.reply_to_message.from_user.first_name
            user_id = message.reply_to_message.from_user.id
        else:
            quote_text = " ".join(message.command[1:])
            user_name = message.from_user.first_name
            user_id = message.from_user.id
        
        if not quote_text:
            message.reply_text("Please provide a quote after .quotly command.")
            return
        
        # Download user's profile picture
        user_photo = None
        photos = client.get_chat_photos(user_id)
        for photo in photos:
            photo_file = client.download_media(photo.file_id)
            with open(photo_file, 'rb') as f:
                user_photo = f.read()
            break  # Only need the first photo
        
        # Generate the quote image
        quote_image = generate_quote_image(quote_text, user_name, user_photo)
        
        # Send the image as a sticker
        message.reply_sticker(sticker=quote_image)

# Note: Replace "Comic Sans MS.ttf" with the correct filename if needed.