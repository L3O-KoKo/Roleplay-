# Ai_Power_Telegram_Bot 🇲🇲  🅱️⭕✝️  🇲🇲
## Creating By 🍁 MarMu + Assistant Codex 🎭

Professional AI roleplay bot powered by **Gemini API + Telegram + persistent memory**.

## Features
- `/start` sends a welcome message and asks users to press the **Menu** button.
- Menu shows **6 story titles** loaded from `stories.json` (supports 5–8 stories).
- When a story is chosen, the bot:
  - takes that roleplay setting,
  - generates a short story summary,
  - starts interactive roleplay chat with the user.
- Per-user memory is stored in `memory.json` to preserve recent conversation turns.

## Files
- `bot.py` — Telegram bot handlers, Gemini integration, and roleplay flow.
- `memory.py` — JSON-based memory store for user state/history.
- `stories.json` — Story menu content (5–8 stories).
- `.env.example` — Environment variable template.
- `requirements.txt` — Python dependencies.

## Setup
1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy environment template and set real credentials:
   ```bash
   cp .env.example .env
   ```
4. Edit `.env`:
   - `TELEGRAM_BOT_TOKEN`
   - `GEMINI_API_KEY`
   - optional `GEMINI_MODEL`

## Run
```bash
python bot.py
```

## Telegram Flow
1. User sends `/start`.
2. Bot responds with welcome + **Menu** button.
3. User presses Menu and sees 6 story titles.
4. User selects a story.
5. Bot introduces/summarizes the story and starts roleplay chat.
6. User and AI continue story-based conversation.
