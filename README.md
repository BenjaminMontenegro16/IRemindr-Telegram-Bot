# IRemindr 🔔
> A Telegram bot that helps you set and manage reminders — straight from your chat.

---

## Features

- Set reminders using natural time formats (`30m`, `2h`, `1d`)
- Persistent storage with PostgreSQL — reminders survive bot restarts
- List all your active reminders
- Delete reminders by ID
- Clear all reminders at once
- Per-user isolation — you only see your own reminders

---

## Commands

| Command | Description | Example |
|--------|-------------|---------|
| `/start` | Welcome message | `/start` |
| `/help` | List all commands | `/help` |
| `/setreminder` | Set a new reminder | `/setreminder 30m Call the dentist` |
| `/listreminders` | Show your active reminders | `/listreminders` |
| `/deletereminder` | Delete a reminder by ID | `/deletereminder 3` |
| `/clearall` | Delete all your reminders | `/clearall` |

---

## Tech Stack

- **Python** — core language
- **python-telegram-bot** — Telegram API wrapper
- **APScheduler** — reminder scheduling
- **PostgreSQL** — persistent reminder storage
- **Railway** — cloud deployment & database hosting
- **python-dotenv** — environment variable management

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/BenjaminMontenegro16/IRemindr-Telegram-Bot
cd IRemindr-Telegram-Bot
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the root directory:

```env
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=your_postgresql_connection_string
DB_HOST=your_db_host
DB_PORT=your_db_port
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
```

### 4. Run the bot
```bash
python main.py
```

---

## Project Structure

```
IRemindr-Telegram-Bot/
├── main.py          # Entry point and command handlers
├── requirements.txt # Project dependencies
├── .env             # Environment variables (not tracked)
├── .gitignore
└── README.md
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `BOT_TOKEN` | Your Telegram bot token from @BotFather |
| `DATABASE_URL` | Full PostgreSQL connection string |
| `DB_HOST` | Database host |
| `DB_PORT` | Database port |
| `DB_NAME` | Database name |
| `DB_USER` | Database user |
| `DB_PASSWORD` | Database password |

---

## What I Learned

- Job scheduling with APScheduler
- Managing environment variables securely
- Deploying a bot with a persistent database on Railway

---

## License

MIT License — feel free to use and modify.

---

*Built by [Benjamin Montenegro Bär](https://github.com/BenjaminMontenegro16)*
