from pyrogram import Client, filters

def add_on_commands(app: Client):
    # Define your commands or event handlers here
    @app.on_message(filters.command("example", prefixes="."))
    def example_command(client, message):
        message.reply_text("This is an example command!")

    # Add more commands or event handlers as needed
    # @app.on_message(filters.command("another_command", prefixes="."))
    # def another_command(client, message):
    #     message.reply_text("This is another command!")

# Note: Do not add client initialization or app.run() here
# It should be done in the main script