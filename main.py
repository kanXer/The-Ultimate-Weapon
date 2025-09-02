import time
import sys

# Import bot functions
from setup import start_bot, build_with_creds

# Print logo only if running as Python script (not EXE/bin)
if not getattr(sys, 'frozen', False):
    def print_logo():
        logo = r"""
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░  _______   _    _   __        __ ░░
░░ |__   __| | |  | |  \ \      / / ░░
░░    | |    | |  | |   \ \ /\ / /  ░░
░░    | |    | |  | |    \ V  V /   ░░
░░    |_|     \____/      \_/\_/    ░░
░░                                  ░░
░░       The Ultimate Weapon        ░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

    Created by Kanxer (Sahil Lala)
"""
        print(logo)
        print("🧠 TUW Bot Setup\n")

    print_logo()
    time.sleep(1)

# ✅ Try to import credentials from embedded config_temp.py
    BOT_TOKEN = input("🔐 Enter your Telegram Bot Token: ").strip()
    CHAT_ID = int(input("💬 Enter your Telegram Chat ID: ").strip())
    use_input = True

# User chooses action only if input was needed
if use_input:
    print("\nSelect action:\n1 → Build executable/bin\n2 → Run bot directly")
    action_choice = input("Enter 1 or 2: >> ").strip()

    if action_choice == "1":
        print('''
Note:-
1. Windows → .exe
2. Linux → .bin
3. Icon optional (.ico/.png)
''')
        exe_name = input("Enter the name of the Executable File: ").strip()
        icon_path = input("🖼 Enter path to icon file or leave empty: ").strip() or None
        build_with_creds(BOT_TOKEN, CHAT_ID, exe_name, icon_path)
    elif action_choice == "2":
        start_bot(BOT_TOKEN, CHAT_ID)
    else:
        print("❌ Invalid action choice.")
else:
    # If credentials are already embedded, just start bot automatically
    start_bot(BOT_TOKEN, CHAT_ID)
