import logging
import os
import importlib.util
import sys
import json
import subprocess
import time
from datetime import datetime
from pyrogram import Client, filters
import psutil
import platform
from dotenv import load_dotenv
import shutil

# Function to clear the console and fill it with a specified background color
def fill_console_with_background(color_code):
    # ANSI escape code to set background color and clear the screen
    background = f'\033[{color_code}m'
    clear_screen = '\033[2J'
    move_cursor_top_left = '\033[H'
    
    # Print the ANSI escape codes
    print(background + clear_screen + move_cursor_top_left, end='')

# Function to display the logo centered with a blue background and animation
def display_logo():
    try:
        fill_console_with_background('44')
        with open('ConsoleLogo.txt', 'r') as f:
            logo = f.read()
        
        # Get console dimensions
        console_width, console_height = shutil.get_terminal_size((80, 20))

        # Split logo into lines
        logo_lines = logo.split('\n')
        logo_height = len(logo_lines)
        logo_width = max(len(line) for line in logo_lines)

        # Calculate starting positions to center the logo
        start_y = max((console_height - logo_height) // 2, 0)
        start_x = max((console_width - logo_width) // 2, 0)

        # Print blank lines to center vertically
        print('\n' * start_y, end='')

        # Print each line of the logo centered with animation
        for line in logo_lines:
            print(' ' * start_x + line)
            time.sleep(0.1)  # Delay to create animation effect

        # Reset color
        print('\033[0m', end='')
        time.sleep(3)
    except IOError:
        logger.error("Error reading ConsoleLogo.txt.")

# Function to perform OOBE
def out_of_box_experience():
    fill_console_with_background('12')  # Gray background

    # Get console dimensions
    console_width, console_height = shutil.get_terminal_size((80, 20))

    # Text to display
    welcome_text = "Welcome to ModuBot!"
    data_prompt = "Enter the required data: {API_ID, API_HASH, OWNER_NICKNAME}"
    hint_text = "You can find {API_ID, API_HASH} at `https://my.telegram.org/`."
    input_prompt = "API_ID: "
    
    # Calculate positions
    welcome_y = max((console_height - 5) // 2 - 1, 0)
    data_prompt_y = welcome_y + 1
    hint_y = max((console_height + 2) // 2 + 1, 0)
    input_y = (console_height // 2)

    # Print text at specified positions
    print('\n' * welcome_y + ' ' * ((console_width - len(welcome_text)) // 2) + welcome_text)
    print(' ' * ((console_width - len(data_prompt)) // 2) + data_prompt)
    print('\n' * (hint_y - data_prompt_y - 1), end='')
    print(' ' * ((console_width - len(hint_text)) // 2) + hint_text)
    
    # Prompt for user input
    api_id = input(' ' * ((console_width - len(input_prompt)) // 2) + input_prompt)
    api_hash = input(' ' * ((console_width - len(input_prompt)) // 2) + "API_HASH: ")
    owner_nickname = input(' ' * ((console_width - len(input_prompt)) // 2) + "OWNER_NICKNAME: ")

    # Save to .env file
    with open('.env', 'w') as env_file:
        env_file.write(f"API_ID={api_id}\nAPI_HASH={api_hash}\nOWNER_NICKNAME={owner_nickname}\n")

# Display the logo before starting the rest of the script
display_logo()

# Check if .env file exists, if not start OOBE
if not os.path.exists('.env'):
    out_of_box_experience()

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load API credentials from environment variables
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')

if not api_id or not api_hash:
    logger.error("API credentials not found. Please set API_ID and API_HASH environment variables.")
    sys.exit(1)

app = Client("my_userbot", api_id=api_id, api_hash=api_hash)

owner_nickname = os.getenv('OWNER_NICKNAME', 'Nobody')
bot_firstname = os.getenv('BOT_FIRSTNAME', 'ModuBot')

loaded_modules = []

sudo_users_file = "SUDOUsers.json"
restart_time_file = "restart_time.txt"

def load_sudo_users():
    try:
        if os.path.exists(sudo_users_file):
            with open(sudo_users_file, "r", encoding="utf-8") as file:
                return json.load(file)
    except json.JSONDecodeError:
        logger.error(f"Error decoding {sudo_users_file}. Using empty list.")
    except IOError:
        logger.error(f"Error reading {sudo_users_file}. Using empty list.")
    return []

sudo_users = load_sudo_users()

def save_sudo_user(user_id):
    if user_id not in sudo_users:
        sudo_users.append(user_id)
        try:
            with open(sudo_users_file, "w", encoding="utf-8") as file:
                json.dump(sudo_users, file)
            logger.info(f"Added user {user_id} to SUDO users.")
        except IOError:
            logger.error(f"Error writing to {sudo_users_file}.")

@app.on_message(filters.command("modules", prefixes=".") & filters.user(sudo_users))
def list_modules(client, message):
    modules_list = "\n".join(loaded_modules) if loaded_modules else "No modules loaded."
    message.reply_text(f"**Loaded modules**:\n\n{modules_list}")

@app.on_message(filters.command("restart", prefixes=".") & filters.user(sudo_users))
def restart_bot(client, message):
    restart_message = message.reply_text("Restarting bot...")
    restart_time = time.time()
    with open(restart_time_file, 'w') as f:
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

    addons_folder = os.path.join(os.path.dirname(__file__), 'AddOns')
    os.makedirs(addons_folder, exist_ok=True)
    module_path = os.path.join(addons_folder, module_name)

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

last_restart_time = datetime.now().strftime("%d/%m(%B) %H:%M:%S")

def add_on_commands(app: Client, loaded_modules, owner_nickname, bot_firstname):
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

For more information on each command, use: .help [command]
"""
        message.reply_text(help_text)

def load_addons(addons_folder):
    for filename in os.listdir(addons_folder):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            module_path = os.path.join(addons_folder, filename)
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

addons_folder = os.path.join(os.path.dirname(__file__), 'AddOns')
load_addons(addons_folder)

add_on_commands(app, loaded_modules, owner_nickname, bot_firstname)

if __name__ == "__main__":
    logger.info("Userbot is starting...")
    
    # Check if this is a restart
    if os.path.exists(restart_time_file):
        try:
            with open(restart_time_file, 'r') as f:
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
            
            os.remove(restart_time_file)
        except Exception as e:
            logger.error(f"Error processing restart information: {e}")
    
    app.run()