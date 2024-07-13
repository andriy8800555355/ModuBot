import logging
import os
import importlib.util
import sys
import json
import subprocess
import time
from datetime import datetime
import requests
from pyrogram import Client, filters
import psutil
import platform
from dotenv import load_dotenv
import shutil
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SUDO_USERS_FILE = "SUDOUsers.json"
RESTART_TIME_FILE = "restart_time.txt"
MODULES_FOLDER = os.path.join(os.path.dirname(__file__), 'Modules')
GITHUB_RAW_URL = "https://raw.githubusercontent.com/andriy8800555355/ModuBot/main/app.py"
MODULES_REPO_URL = "https://api.github.com/repos/andriy8800555355/ModuBotModules/contents"
CHECK_INTERVAL = 60  # seconds

# Utility Functions
def fill_console_with_background(color_code):
    background = f'\033[{color_code}m'
    clear_screen = '\033[2J'
    move_cursor_top_left = '\033[H'
    print(background + clear_screen + move_cursor_top_left, end='')

def display_logo():
    try:
        fill_console_with_background('44')
        with open('ConsoleLogo.txt', 'r') as f:
            logo = f.read()
        
        console_width, console_height = shutil.get_terminal_size((80, 20))
        logo_lines = logo.split('\n')
        logo_height = len(logo_lines)
        logo_width = max(len(line) for line in logo_lines)
        start_y = max((console_height - logo_height) // 2, 0)
        start_x = max((console_width - logo_width) // 2, 0)

        print('\n' * start_y, end='')
        for line in logo_lines:
            print(' ' * start_x + line)
            time.sleep(0.1)
        print('\033[0m', end='')
        time.sleep(3)
    except IOError:
        logger.error("Error reading ConsoleLogo.txt.")

def out_of_box_experience():
    fill_console_with_background('12')
    console_width, console_height = shutil.get_terminal_size((80, 20))
    welcome_text = "Welcome to ModuBot!"
    data_prompt = "Enter the required data: {API_ID, API_HASH, OWNER_NICKNAME}"
    hint_text = "You can find {API_ID, API_HASH} at `https://my.telegram.org/`."
    input_prompt = "API_ID: "
    
    welcome_y = max((console_height - 5) // 2 - 1, 0)
    data_prompt_y = welcome_y + 1
    hint_y = max((console_height + 2) // 2 + 1, 0)
    input_y = (console_height // 2)

    print('\n' * welcome_y + ' ' * ((console_width - len(welcome_text)) // 2) + welcome_text)
    print(' ' * ((console_width - len(data_prompt)) // 2) + data_prompt)
    print('\n' * (hint_y - data_prompt_y - 1), end='')
    print(' ' * ((console_width - len(hint_text)) // 2) + hint_text)
    
    api_id = input(' ' * ((console_width - len(input_prompt)) // 2) + input_prompt)
    api_hash = input(' ' * ((console_width - len(input_prompt)) // 2) + "API_HASH: ")
    owner_nickname = input(' ' * ((console_width - len(input_prompt)) // 2) + "OWNER_NICKNAME: ")

    with open('.env', 'w') as env_file:
        env_file.write(f"API_ID={api_id}\nAPI_HASH={api_hash}\nOWNER_NICKNAME={owner_nickname}\n")

def load_sudo_users():
    try:
        if os.path.exists(SUDO_USERS_FILE):
            with open(SUDO_USERS_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
    except (json.JSONDecodeError, IOError):
        logger.error(f"Error reading {SUDO_USERS_FILE}. Using empty list.")
    return []

def save_sudo_user(user_id):
    if user_id not in sudo_users:
        sudo_users.append(user_id)
        try:
            with open(SUDO_USERS_FILE, "w", encoding="utf-8") as file:
                json.dump(sudo_users, file)
            logger.info(f"Added user {user_id} to SUDO users.")
        except IOError:
            logger.error(f"Error writing to {SUDO_USERS_FILE}.")

def check_for_updates():
    try:
        response = requests.get(GITHUB_RAW_URL)
        if response.status_code == 200:
            github_content = response.text
            with open(__file__, 'r') as local_file:
                local_content = local_file.read()
            if github_content != local_content:
                logger.info("Update available for the main script.")
                return True
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")
    return False

def update_main_script():
    try:
        response = requests.get(GITHUB_RAW_URL)
        if response.status_code == 200:
            with open(__file__, 'w') as local_file:
                local_file.write(response.text)
            logger.info("Main script updated successfully.")
            return True
    except Exception as e:
        logger.error(f"Error updating main script: {e}")
    return False

def load_modules(app):
    for filename in os.listdir(MODULES_FOLDER):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            module_path = os.path.join(MODULES_FOLDER, filename)
            try:
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if callable(attr) and attr_name.startswith("add_on"):
                        logger.info(f"Loading handler: {attr_name} from {module_name}")
                        attr(app)
                        loaded_modules.append(module_name)
            except Exception as e:
                logger.error(f"Error loading module {module_name}: {e}")

def notify_update_available():
    try:
        app.send_message("me", "An update is available for the main script. Please restart the bot to apply the update.")
    except Exception as e:
        logger.error(f"Error sending update notification: {e}")

def start_update_checker():
    while True:
        if check_for_updates():
            notify_update_available()
        time.sleep(CHECK_INTERVAL)

# Initialize
display_logo()
if not os.path.exists('.env'):
    out_of_box_experience()
load_dotenv()

api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
if not api_id or not api_hash:
    logger.error("API credentials not found. Please set API_ID and API_HASH environment variables.")
    sys.exit(1)

app = Client("my_userbot", api_id=api_id, api_hash=api_hash)
owner_nickname = os.getenv('OWNER_NICKNAME', 'Nobody')
bot_firstname = os.getenv('BOT_FIRSTNAME', 'ModuBot')
loaded_modules = []
sudo_users = load_sudo_users()
last_restart_time = datetime.now().strftime("%d/%m(%B) %H:%M:%S")

# Command Handlers
@app.on_message(filters.command("modules", prefixes=".") & filters.user(sudo_users))
def list_modules(client, message):
    modules_list = "\n".join(loaded_modules) if loaded_modules else "No modules loaded."
    message.reply_text(f"**Loaded modules**:\n\n{modules_list}")

@app.on_message(filters.command("restart", prefixes=".") & filters.user(sudo_users))
def restart_bot(client, message):
    restart_message = message.reply_text("Restarting bot...")
    restart_time = time.time()
    with open(RESTART_TIME_FILE, 'w') as f:
        f.write(f"{restart_time}\n{restart_message.chat.id}\n{restart_message.id}")
    logger.info("Restarting the bot...")
    os.execl(sys.executable, sys.executable, *sys.argv)

@app.on_message(filters.command("addsudo", prefixes=".") & filters.me)
def add_sudo(client, message):
    if not message.reply_to_message:
        message.reply_text("Please reply to the user you want to give SUDO access to.")
        return
    user_id = message.reply_to_message.from_user.id
    if user_id in sudo_users:
        message.reply_text("User already has SUDO access.")
    else:
        save_sudo_user(user_id)
        message.reply_text(f"User {user_id} has been given SUDO access.")

@app.on_message(filters.command("install", prefixes=".") & filters.user(sudo_users))
def install_library(client, message):
    command_parts = message.text.split()
    if len(command_parts) != 2:
        message.reply_text("Usage: .install library_name")
        return
    library_name = command_parts[1]
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", library_name])
        message.reply_text(f"Library `{library_name}` installed successfully.")
    except subprocess.CalledProcessError as e:
        message.reply_text(f"Failed to install library `{library_name}`.")
        logger.error(f"Error installing library `{library_name}`: {e}")

# Load modules and start the bot
load_modules(app)

update_checker_thread = threading.Thread(target=start_update_checker, daemon=True)
update_checker_thread.start()

logger.info("Starting the bot...")
app.run()

#test