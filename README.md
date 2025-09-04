# Discord Personal Data Bot

A Discord bot that stores and manages personal data through Direct Messages (DMs). The bot automatically categorizes and stores text, passwords, emails, links, and extracts text from images using OCR.

## Features

- **DM Only**: Only responds to Direct Messages, ignores server messages
- **Auto-categorization**: Automatically detects and stores:
  - Passwords (with labels)
  - Email addresses
  - URLs and links
  - Notes and text
  - Image text (via OCR)
- **Persistent Storage**: SQLite database for reliable data storage
- **Command Interface**: Responds to specific trigger commands
- **OCR Support**: Extracts text from uploaded images using Tesseract

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `!wake` or `!hey` | **Wake up bot and get conversation summary** | `!wake` |
| `!get password <label>` | Retrieve a saved password | `!get password gmail` |
| `!get credentials` | Get all saved credentials (username/password) | `!get credentials` |
| `!get credential <label>` | Get specific credentials by label | `!get credential Gmail` |
| `!get notes` | Get all saved notes | `!get notes` |
| `!get emails` | Get all saved emails | `!get emails` |
| `!get links` | Get all saved links | `!get links` |
| `!list` | List all stored data categories | `!list` |
| `!clear` | Clear all your data | `!clear` |
| `!recent [number]` | Show recent messages | `!recent 10` |
| `!search <term>` | Search through stored data | `!search password` |
| `!help` | Show help message | `!help` |

## Auto-detection Examples

- **Credentials**: 
  - `username: john password: mypass123`
  - `Gmail - username: john@gmail.com password: mypass123`
  - `Netflix: user: john@email.com pass: mypass123`
  - `Spotify - john: mypass123`
- **Passwords**: `password: gmail mypassword123`
- **Notes**: Any regular text message
- **Emails**: `john@example.com` (automatically detected)
- **Links**: `https://github.com/user/repo` (automatically detected)
- **Images**: Upload any image, OCR text will be extracted and stored

## Installation

### Prerequisites

1. **Python 3.8+**
2. **Tesseract OCR** (for image text extraction)

#### Installing Tesseract

**Windows:**
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install and note the installation path (usually `C:\Program Files\Tesseract-OCR\tesseract.exe`)
3. Add to PATH or set `TESSERACT_PATH` environment variable

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install tesseract-ocr
```

**Replit:**
```bash
# In Replit shell
sudo apt update
sudo apt install tesseract-ocr
```

### Setup

1. **Clone or download the bot files**

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Create a Discord Bot:**
   - Go to https://discord.com/developers/applications
   - Create a new application
   - Go to "Bot" section
   - Create a bot and copy the token
   - Enable "Message Content Intent" in Bot permissions

4. **Set environment variables:**
```bash
# Required
export DISCORD_BOT_TOKEN="your_bot_token_here"

# Optional (Windows only if Tesseract not in PATH)
export TESSERACT_PATH="C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
```

**Windows (PowerShell):**
```powershell
$env:DISCORD_BOT_TOKEN="your_bot_token_here"
$env:TESSERACT_PATH="C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
```

**Windows (Command Prompt):**
```cmd
set DISCORD_BOT_TOKEN=your_bot_token_here
set TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

5. **Run the bot:**
```bash
python bot.py
```

### Replit Setup

1. **Create a new Repl** and upload all bot files
2. **Install Tesseract OCR** in the Replit shell:
   ```bash
   sudo apt update
   sudo apt install tesseract-ocr
   ```
3. **Set environment variables** in Replit Secrets:
   - `DISCORD_BOT_TOKEN`: Your Discord bot token
4. **Run the bot** - it will automatically start the keep-alive server
5. **The bot will stay awake** with the built-in keep-alive mechanism

**Replit Features:**
- ✅ Automatic keep-alive server (port 8080)
- ✅ On-demand processing with `!wake` command
- ✅ Conversation history analysis
- ✅ Persistent SQLite database

## File Structure

```
discord-personal-bot/
├── bot.py              # Main bot entry point
├── storage.py          # Database operations
├── ocr.py             # Image OCR processing
├── commands.py        # Command handling
├── config.py          # Configuration settings
├── requirements.txt   # Python dependencies
├── README.md         # This file
└── user_data.db      # SQLite database (created automatically)
```

## Configuration

The bot can be configured using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DISCORD_BOT_TOKEN` | Required | Discord bot token |
| `DATABASE_PATH` | `user_data.db` | SQLite database file path |
| `TESSERACT_PATH` | Auto-detect | Path to Tesseract executable |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FILE` | `bot.log` | Log file path |
| `MAX_RECENT_MESSAGES` | `50` | Max messages for recent/search |
| `MAX_SEARCH_RESULTS` | `10` | Max search results to display |

## Usage Examples

### Storing Data
```
You: password: gmail mypassword123
Bot: (stores password, no response)

You: john@example.com
Bot: (stores email, no response)

You: https://github.com/user/repo
Bot: (stores link, no response)

You: Remember to buy groceries tomorrow
Bot: (stores as note, no response)
```

### Retrieving Data
```
You: !get password gmail
Bot: Password for 'gmail': `mypassword123`

You: !get notes
Bot: Your Notes:
1. Remember to buy groceries tomorrow
2. Meeting at 3 PM today

You: !list
Bot: Your Stored Data:
📝 Total Messages: 15
🔑 Passwords: 3
📄 Notes: 8
📧 Emails: 2
🔗 Links: 2
```

## Security Notes

- All data is stored locally in SQLite database
- Bot only responds to DMs, not server messages
- No data is shared between users
- Consider enabling encryption for sensitive data (see config.py)

## Troubleshooting

### Common Issues

1. **"Tesseract not found" error:**
   - Install Tesseract OCR
   - Set `TESSERACT_PATH` environment variable (Windows)

2. **"Invalid Discord bot token" error:**
   - Check your bot token is correct
   - Ensure bot has "Message Content Intent" enabled

3. **Bot not responding to DMs:**
   - Make sure you're sending DMs, not server messages
   - Check bot permissions

4. **OCR not working:**
   - Verify Tesseract installation
   - Check image format is supported (PNG, JPG, etc.)

### Logs

Check `bot.log` for detailed error messages and debugging information.

## Development

### Adding New Commands

1. Add command logic to `commands.py`
2. Update the `handle_command` method
3. Add help text to `_handle_help` method

### Extending Storage

1. Add new table to `storage.py` `initialize` method
2. Add corresponding storage/retrieval methods
3. Update `get_all_categories` method

## License

This project is open source. Use responsibly and ensure compliance with Discord's Terms of Service.
