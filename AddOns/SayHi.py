from pyrogram import Client, filters

def add_on1(app: Client):
    @app.on_message(filters.command("SayHI", prefixes="."))
    def addon1(client, message):
        message.reply_text("Say HI to new Galaxy Note!")
