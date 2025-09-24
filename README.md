# Telegram Brute Force Bot

A Telegram bot that performs a brute force attack on a system user's password via Telegram commands.

## ⚠️ Warning

**For educational purposes and testing on your own systems ONLY.** Use for unauthorized access is illegal.

## Description

The bot allows remote control of password guessing via Telegram. It uses multithreading to speed up the process.

## Installation

1. Install dependencies:
```bash
pip install pyTelegramBotAPI
```
2. Set up the bot:
- Create a bot via @BotFather
- Replace `BOT_TOKEN = 'Your-API-key'` with your token in the code
- Change `TARGET_USER = "admin"` to the desired user
## Usage

### Bot commands:

**/start <max_length> [initial_combination] [number_of_threads]** - Launch brute force
- Example: `/start 5`
- Example: `/start 6 abc 50`

**/speed <number_of_threads>** - Change the number of threads
- Example: `/speed 100`

**/stop** - Stop the process

**/status** - Current status

**/stats** - Detailed statistics

**/max_threads <max_threads>** - Set maximum threads

## Technical Details

- **Target User**: Default: "admin"
- **Character Set**: Letters, numbers, special characters
- **Maximum Threads**: 200
- **Verification Method**: `su` command

## Requirements

- Python 3.6+
- Linux (requires the `su` command)

## Important

1. Use only with permission
2. A large number of threads may overload the system
3. The bot token must be kept secret
4. Activity is easily detectable
