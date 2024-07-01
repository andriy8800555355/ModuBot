import logging
import os
import importlib.util
import sys
import json
import subprocess
from datetime import datetime
from pyrogram import Client, filters
import psutil
import platform

# Set up logging
logging.basicConfig(level=logging.INFO)

# Define API credentials
api_id = '22860593'  # Replace with your API ID
api_hash = '2c8e567c3ffd9fc454bb23fc89c90613'  # Replace with your API hash

# Create a new Client instance
app = Client("my_userbot", api_id=api_id, api_hash=api_hash)

owner_nickname = "Nobody"
bot_firstname = "ModuBot"

loaded_modules = []

# Approved users storage
approved_users_file = "approvedusers.json"

def load_approved_users():
    if os.path.exists(approved_users_file):
        with open(approved_users_file, "r", encoding="utf-8") as file:
            return json.load(file)
    return []

approved_users = load_approved_users()

def save_approved_user(user_id):
    approved_users.append(user_id)
    with open(approved_users_file, "w", encoding="utf-8") as file:
        json.dump(approved_users, file)

@app.on_message(filters.command("modules", prefixes=".") & filters.user(approved_users))
def list_modules(client, message):
    modules_list = "\n".join(loaded_modules) if loaded_modules else "No modules loaded."
    reply_message = f"**Loaded modules**:\n\n{modules_list}"
    message.reply_text(reply_message)

@app.on_message(filters.command("restart", prefixes=".") & filters.user(approved_users))
def restart_bot(client, message):
    message.reply_text("Restarting bot...")
    restart_script()

def restart_script():
    python = sys.executable
    os.execl(python, python, *sys.argv)

@app.on_message(filters.command("givehimaccess", prefixes=".") & filters.me)
def give_access(client, message):
    if not message.reply_to_message:
        message.reply_text("Please reply to the user you want to give access to.")
        return

    user_id = message.reply_to_message.from_user.id
    if user_id in approved_users:
        message.reply_text("User already has access.")
    else:
        save_approved_user(user_id)
        message.reply_text(f"User {user_id} has been given access.")

@app.on_message(filters.command("install", prefixes=".") & filters.user(approved_users))
def install_library(client, message):
    command_parts = message.text.split()
    if len(command_parts) != 2:
        message.reply_text("Usage: .install library_name")
        return

    library_name = command_parts[1]

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", library_name])
        message.reply_text(f"Library {library_name} installed successfully.")
    except subprocess.CalledProcessError as e:
        message.reply_text(f"Failed to install library {library_name}. Error: {e}")

@app.on_message(filters.command("pull", prefixes=".") & filters.user(approved_users) & filters.reply)
def pull_module(client, message):
    if not message.reply_to_message.text:
        message.reply_text("Please reply to a message containing the module script as text.")
        return

    script_content = message.reply_to_message.text

    # Extract module name from the command
    command_parts = message.text.split()
    if len(command_parts) != 2:
        message.reply_text("Usage: .pull NameOfModule.py")
        return

    module_name = command_parts[1]
    if not module_name.endswith(".py"):
        message.reply_text("The module name must end with .py")
        return

    addons_folder = os.path.join(os.path.dirname(__file__), 'AddOns')
    os.makedirs(addons_folder, exist_ok=True)
    module_path = os.path.join(addons_folder, module_name)

    # Save the module script, overwrite if it already exists
    with open(module_path, "w", encoding="utf-8") as module_file:
        module_file.write(script_content)

    message.reply_text(f"Module {module_name} saved. Restarting bot...")
    restart_script()

# Add last restart time
last_restart_time = datetime.now().strftime("%d/%m(%B) %H:%M:%S")

def add_on_commands(app: Client, loaded_modules, owner_nickname, bot_firstname):
    @app.on_message(filters.command("start", prefixes="."))
    def start_command(client, message):
        # Send the logo.gif
        message.reply_document("logo.gif")
        
        # Gather system resource usage
        memory = psutil.virtual_memory()
        cpu_usage = psutil.cpu_percent(interval=1)
        process = psutil.Process(os.getpid())
        ram_usage = process.memory_info().rss / 1024 ** 2
        host_info = platform.uname()
        
        # Prepare the welcome message
        current_time = datetime.now().strftime("%d/%m(%B) %H:%M:%S")
        modules_list = "\n".join(loaded_modules) if loaded_modules else "No modules loaded."
        
        welcome_message = f"""
**Welcome to ModuBot!**

Time of last reboot: {last_restart_time}

**Installed modules**
{modules_list}

**Userbot owner**: **{owner_nickname}**

**System Info**
CPU Usage: {cpu_usage}%
Memory Usage: {memory.percent}%
RAM Usage: {ram_usage:.2f} MB

**Host Info**
System: {host_info.system}
Node Name: {host_info.node}
Release: {host_info.release}
Version: {host_info.version}
Machine: {host_info.machine}
Processor: {host_info.processor}

Enjoy!
"""
        # Send the welcome message
        message.reply_text(welcome_message)

# Function to dynamically load add-ons
def load_addons(addons_folder):
    for filename in os.listdir(addons_folder):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            module_path = os.path.join(addons_folder, filename)
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            try:
                with open(module_path, "r", encoding="utf-8") as module_file:
                    code = module_file.read()
            except UnicodeDecodeError:
                with open(module_path, "r", encoding="latin-1") as module_file:
                    code = module_file.read()
            exec(code, module.__dict__)
            # Find and call handler functions automatically
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if callable(attr) and attr_name.startswith("add_on"):
                    print(f"Loading handler: {attr_name} from {module_name}")
                    attr(app)
                    loaded_modules.append(module_name)

# Note: Replace SUDO_USERS with your actual list of admin user IDs
SUDO_USERS = [7001021431]

# Load add-ons
addons_folder = os.path.join(os.path.dirname(__file__), 'AddOns')
load_addons(addons_folder)

# Add additional commands
add_on_commands(app, loaded_modules, owner_nickname, bot_firstname)

# Start the bot
if __name__ == "__main__":
    print("Userbot is running...")
    app.run()
