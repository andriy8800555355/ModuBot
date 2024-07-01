import json
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions
from datetime import datetime, timedelta

# In-memory storage for user warnings and mute statuses
data_file = 'user_data.json'
user_warnings = {}
user_mutes = {}

def load_data():
    global user_warnings, user_mutes
    try:
        with open(data_file, 'r') as f:
            data = json.load(f)
            user_warnings = data.get('warnings', {})
            user_mutes = data.get('mutes', {})
    except FileNotFoundError:
        pass

def save_data():
    with open(data_file, 'w') as f:
        json.dump({'warnings': user_warnings, 'mutes': user_mutes}, f)

def parse_duration(duration):
    """Parse duration string into seconds."""
    amount = int(duration[:-1])
    unit = duration[-1]
    if unit == 's':
        return amount
    elif unit == 'm':
        return amount * 60
    elif unit == 'h':
        return amount * 3600
    elif unit == 'd':
        return amount * 86400
    else:
        raise ValueError("Invalid duration unit")

def admin_commands(app: Client):
    @app.on_message(filters.command("ban", prefixes=".") & filters.user(SUDO_USERS))
    def ban(client, message):
        if not message.reply_to_message and len(message.command) < 3:
            message.reply_text("Usage: .ban <first_name> <duration> or reply to a message with .ban <duration>")
            return

        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            first_name = message.reply_to_message.from_user.first_name
            duration = message.command[1] if len(message.command) > 1 else '1d'  # Default to 1 day if no duration is provided
        else:
            first_name = message.command[1]
            duration = message.command[2]
            user_id = get_user_id_by_name(client, message.chat.id, first_name)
        
        if not user_id:
            message.reply_text(f"User {first_name} not found.")
            return

        try:
            ban_duration = parse_duration(duration)
        except ValueError:
            message.reply_text("Invalid duration format. Use s, m, h, or d for seconds, minutes, hours, or days respectively.")
            return

        until_date = datetime.utcnow() + timedelta(seconds=ban_duration)
        client.ban_chat_member(message.chat.id, user_id, until_date=until_date)
        message.reply_text(f"User {first_name} has been banned for {duration}.")

    @app.on_message(filters.command("mute", prefixes=".") & filters.user(SUDO_USERS))
    def mute(client, message):
        if not message.reply_to_message and len(message.command) < 3:
            message.reply_text("Usage: .mute <first_name> <duration> or reply to a message with .mute <duration>")
            return

        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            first_name = message.reply_to_message.from_user.first_name
            duration = message.command[1] if len(message.command) > 1 else '1h'  # Default to 1 hour if no duration is provided
        else:
            first_name = message.command[1]
            duration = message.command[2]
            user_id = get_user_id_by_name(client, message.chat.id, first_name)
        
        if not user_id:
            message.reply_text(f"User {first_name} not found.")
            return

        try:
            mute_duration = parse_duration(duration)
        except ValueError:
            message.reply_text("Invalid duration format. Use s, m, h, or d for seconds, minutes, hours, or days respectively.")
            return

        until_date = datetime.utcnow() + timedelta(seconds=mute_duration)
        permissions = ChatPermissions(can_send_messages=False)
        client.restrict_chat_member(message.chat.id, user_id, permissions=permissions, until_date=until_date)
        message.reply_text(f"User {first_name} has been muted for {duration}.")

        user_mutes[user_id] = until_date.timestamp()
        save_data()

    @app.on_message(filters.command("warn", prefixes=".") & filters.user(SUDO_USERS))
    def warn(client, message):
        if not message.reply_to_message:
            message.reply_text("Usage: .warn (reply to the user's message)")
            return

        user_id = message.reply_to_message.from_user.id
        first_name = message.reply_to_message.from_user.first_name

        if user_id not in user_warnings:
            user_warnings[user_id] = 0

        user_warnings[user_id] += 1
        message.reply_text(f"User {first_name} has been warned. Total warnings: {user_warnings[user_id]}.")

        if user_warnings[user_id] >= 3:
            permissions = ChatPermissions(can_send_messages=False)
            client.restrict_chat_member(message.chat.id, user_id, permissions=permissions)
            message.reply_text(f"User {first_name} has been muted indefinitely due to 3 warnings.")
            user_mutes[user_id] = "forever"

        save_data()

    @app.on_message(filters.command("unban", prefixes=".") & filters.user(SUDO_USERS))
    def unban(client, message):
        if not message.reply_to_message and len(message.command) < 2:
            message.reply_text("Usage: .unban <first_name> or reply to a message with .unban")
            return

        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            first_name = message.reply_to_message.from_user.first_name
        else:
            first_name = message.command[1]
            user_id = get_user_id_by_name(client, message.chat.id, first_name)
        
        if not user_id:
            message.reply_text(f"User {first_name} not found.")
            return

        client.unban_chat_member(message.chat.id, user_id)
        message.reply_text(f"User {first_name} has been unbanned.")

    @app.on_message(filters.command("unmute", prefixes=".") & filters.user(SUDO_USERS))
    def unmute(client, message):
        if not message.reply_to_message and len(message.command) < 2:
            message.reply_text("Usage: .unmute <first_name> or reply to a message with .unmute")
            return

        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            first_name = message.reply_to_message.from_user.first_name
        else:
            first_name = message.command[1]
            user_id = get_user_id_by_name(client, message.chat.id, first_name)
        
        if not user_id:
            message.reply_text(f"User {first_name} not found.")
            return

        permissions = ChatPermissions(can_send_messages=True)
        client.restrict_chat_member(message.chat.id, user_id, permissions=permissions)
        message.reply_text(f"User {first_name} has been unmuted.")

        if user_id in user_mutes:
            del user_mutes[user_id]
            save_data()

    @app.on_message(filters.command("unwarn", prefixes=".") & filters.user(SUDO_USERS))
    def unwarn(client, message):
        if not message.reply_to_message:
            message.reply_text("Usage: .unwarn (reply to the user's message)")
            return

        user_id = message.reply_to_message.from_user.id
        first_name = message.reply_to_message.from_user.first_name

        if user_id in user_warnings:
            user_warnings[user_id] -= 1
            if user_warnings[user_id] <= 0:
                del user_warnings[user_id]
            message.reply_text(f"One warning removed from user {first_name}. Total warnings: {user_warnings.get(user_id, 0)}.")
            save_data()
        else:
            message.reply_text(f"User {first_name} has no warnings.")

# Note: Replace SUDO_USERS with your actual list of admin user IDs
SUDO_USERS = [7001021431]

def add_on(app: Client):
    load_data()
    admin_commands(app)
