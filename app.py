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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SUDO_USERS_FILE = "SUDOUsers.json"
RESTART_TIME_FILE = "restart_time.txt"
MODULES_FOLDER = os.path.join(os.path.dirname(__file__), 'Modules')
GITHUB_RAW_URL = "https://raw.githubusercontent.com/andriy8800555355/ModuBot/main/app.py"
MODULES_REPO_URL = "https://api.github.com/repos/andriy8800555355/ModuBotModules/contents"

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
        message.reply_text(f"Library {library_name} installed successfully.")
        logger.info(f"Installed library: {library_name}")
    except subprocess.CalledProcessError as e:
        error_message = f"Failed to install library {library_name}. Error: {e}"
        message.reply_text(error_message)
        logger.error(error_message)

@app.on_message(filters.command("commands", prefixes="."))
def show_commands(client, message):
    try:
        with open('commands.txt', 'r', encoding='utf-8') as file:
            commands_text = file.read()
        message.reply_text(f"**Commands**:\n\n{commands_text}")
    except FileNotFoundError:
        message.reply_text("The commands.txt file was not found.")
    except IOError as e:
        message.reply_text(f"Error reading commands.txt: {e}")

@app.on_message(filters.command("pull", prefixes=".") & filters.user(sudo_users) & filters.reply)
def pull_module(client, message):
    if not message.reply_to_message.text:
        message.reply_text("Please reply to a message containing the module script as text.")
        return
    script_content = message.reply_to_message.text
    command_parts = message.text.split()
    if len(command_parts) != 2:
        message.reply_text("Usage: .pull NameOfModule.py")
        return
    module_name = command_parts[1]
    if not module_name.endswith(".py"):
        message.reply_text("The module name must end with .py")
        return
    os.makedirs(MODULES_FOLDER, exist_ok=True)
    module_path = os.path.join(MODULES_FOLDER, module_name)
    try:
        with open(module_path, "w", encoding="utf-8") as module_file:
            module_file.write(script_content)
        logger.info(f"Module {module_name} saved successfully.")
        message.reply_text(f"Module {module_name} saved. Restarting bot...")
        restart_bot(client, message)
    except IOError:
        error_message = f"Error saving module {module_name}."
        message.reply_text(error_message)
        logger.error(error_message)

@app.on_message(filters.command("start", prefixes=".") & filters.user(sudo_users))
def start_command(client, message):
    try:
        message.reply_document("logo.gif")
    except Exception as e:
        logger.error(f"Error sending logo: {e}")

    memory = psutil.virtual_memory()
    cpu_usage = psutil.cpu_percent(interval=1)
    process = psutil.Process(os.getpid())
    ram_usage = process.memory_info().rss / 1024 ** 2
    host_info = platform.uname()
    
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
    message.reply_text(welcome_message)

@app.on_message(filters.command("help", prefixes=".") & filters.user(sudo_users))
def help_command(client, message):
    help_text = """
**Available Commands**

.modules - List loaded modules
.restart - Restart the bot
.addsudo - Add a user to SUDO list (reply to a message)
.install [library] - Install a Python library
.pull [module.py] - Pull and install a new module (reply to code)
.start - Display bot information
.help - Show this help message
.update - Check for updates and update the main script
.downloadmodule [MODULE_NAME.py] - Download a module from the repository

For more information on each command, use: .help [command]
"""
    message.reply_text(help_text)

@app.on_message(filters.command("update", prefixes=".") & filters.user(sudo_users))
def update_command(client, message):
    if check_for_updates():
        if update_main_script():
            message.reply_text("Main script updated successfully. Restarting...")
            restart_bot(client, message)
        else:
            message.reply_text("Failed to update the main script. Please try again later.")
    else:
        message.reply_text("No updates available.")

@app.on_message(filters.command("downloadmodule", prefixes=".") & filters.user(sudo_users))
def download_module(client, message):
    command_parts = message.text.split()
    if len(command_parts) != 2:
        message.reply_text("Usage: .downloadmodule MODULE_NAME.py")
        return
    
    module_name = command_parts[1]
    try:
        response = requests.get(f"{MODULES_REPO_URL}/{module_name}")
        if response.status_code == 200:
            module_info = response.json()
            module_content = requests.get(module_info['download_url']).text
            
            os.makedirs(MODULES_FOLDER, exist_ok=True)
            module_path = os.path.join(MODULES_FOLDER, module_name)
            
            with open(module_path, 'w', encoding='utf-8') as module_file:
                module_file.write(module_content)
            
            logger.info(f"Module {module_name} downloaded successfully.")
            message.reply_text(f"Module {module_name} downloaded and saved. Restarting bot...")
            restart_bot(client, message)
        else:
            message.reply_text(f"Module {module_name} not found in the repository.")
    except Exception as e:
        error_message = f"Error downloading module {module_name}: {e}"
        message.reply_text(error_message)
        logger.error(error_message)

# Main execution
if __name__ == "__main__":
    logger.info("ModuBot is starting...")
    
    # Check for updates on startup
    if check_for_updates():
        logger.info("Update available. Updating main script...")
        if update_main_script():
            logger.info("Main script updated successfully. Restarting...")
            os.execl(sys.executable, sys.executable, *sys.argv)
    
    # Check if this is a restart
    if os.path.exists(RESTART_TIME_FILE):
        try:
            with open(RESTART_TIME_FILE, 'r') as f:
                restart_time, chat_id, message_id = f.read().strip().split('\n')
                restart_time = float(restart_time)
                chat_id = int(chat_id)
                message_id = int(message_id)
            
            restart_duration = time.time() - restart_time
            
            @app.on_message(filters.chat(chat_id))
            async def edit_restart_message(client, message):
                if message.id == message_id:
                    await message.edit_text(f"Restart complete! Time taken to restart: {restart_duration:.2f} seconds")
                    # Remove this handler after executing once
                    app.remove_handler(edit_restart_message)
            
            os.remove(RESTART_TIME_FILE)
        except Exception as e:
            logger.error(f"Error processing restart information: {e}")
    
    # Load modules
    load_modules(app)
    
    # Start the bot
    app.run()

#TestUpdate=)