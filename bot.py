from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from memory import MemoryStore


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

MODEL = genai.GenerativeModel(GEMINI_MODEL) if GEMINI_API_KEY else None
MEMORY = MemoryStore("memory.json")


def load_stories(path: str = "stories.json") -> list[dict]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        stories = json.load(f)

    if not (5 <= len(stories) <= 8):
        raise ValueError("stories.json must contain 5 to 8 story entries.")

    return stories


STORIES = load_stories()
STORY_MAP = {story["id"]: story for story in STORIES}


def menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("📚 Menu", callback_data="menu")]]
    )


def stories_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(story["title"], callback_data=f"story:{story['id']}")]
        for story in STORIES
    ]
    return InlineKeyboardMarkup(rows)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user:
        MEMORY.ensure_user(update.effective_user.id)

    text = (
        "👋 Welcome to *AI Power Roleplay Bot*!\n\n"
        "Choose a story-driven adventure and I will roleplay with you inside that world.\n"
        "Press the *Menu* button below to begin."
    )
    await update.message.reply_text(text, reply_markup=menu_keyboard(), parse_mode="Markdown")


async def on_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "Pick a story title (5-8 options available):",
        reply_markup=stories_keyboard(),
    )


def _fallback_summary(story: dict) -> str:
    return (
        f"*{story['title']}*\n"
        f"Setting: {story['setting']}\n"
        f"Summary: {story['premise']}"
    )


def _build_roleplay_prompt(story: dict, history: list[dict[str, str]], user_text: str) -> str:
    history_lines = "\n".join(f"{h['role']}: {h['text']}" for h in history[-10:])
    return (
        "You are a collaborative roleplay partner on Telegram.\n"
        "Stay in character and continue the selected story with vivid but concise scene writing.\n"
        "Ask a question or offer 2 choices when appropriate.\n"
        "Never break character unless safety requires it.\n\n"
        f"Selected Story Title: {story['title']}\n"
        f"Setting: {story['setting']}\n"
        f"Core Premise: {story['premise']}\n\n"
        f"Conversation History:\n{history_lines or '(none yet)'}\n\n"
        f"User Message: {user_text}\n\n"
        "Now reply as the roleplay AI character."
    )


async def on_story_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    _, story_id = query.data.split(":", maxsplit=1)
    story = STORY_MAP.get(story_id)
    if not story:
        await query.message.reply_text("Story not found. Please press Menu and choose again.")
        return

    user_id = query.from_user.id
    MEMORY.set_story(user_id, story)

    summary_text = _fallback_summary(story)
    if MODEL:
        try:
            prompt = (
                "Summarize this roleplay story in 3-4 lines and end with an in-world hook question.\n"
                f"Title: {story['title']}\n"
                f"Setting: {story['setting']}\n"
                f"Premise: {story['premise']}"
            )
            response = MODEL.generate_content(prompt)
            if response.text:
                summary_text = response.text
        except Exception as exc:
            logger.warning("Gemini summary failed, using fallback summary: %s", exc)

    await query.message.reply_text(
        f"🎭 Great choice! We'll play: *{story['title']}*\n\n{summary_text}\n\n"
        "Send your first action or dialogue to start roleplay.",
        parse_mode="Markdown",
    )


async def on_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return

    user_id = update.effective_user.id
    story = MEMORY.get_story(user_id)
    if not story:
        await update.message.reply_text(
            "Please press /start and choose a story from Menu first."
        )
        return

    user_text = update.message.text.strip()
    MEMORY.append_turn(user_id, "user", user_text)
    history = MEMORY.get_history(user_id)

    if not MODEL:
        fallback = (
            f"(Gemini key missing) You said: {user_text}\n"
            "I can continue once GEMINI_API_KEY is configured."
        )
        MEMORY.append_turn(user_id, "assistant", fallback)
        await update.message.reply_text(fallback)
        return

    try:
        prompt = _build_roleplay_prompt(story, history, user_text)
        response = MODEL.generate_content(prompt)
        answer = response.text.strip() if response.text else "I pause silently, awaiting your next move."
    except Exception as exc:
        logger.exception("Gemini roleplay generation failed: %s", exc)
        answer = "A strange interference hits the scene. Try another action in a moment."

    MEMORY.append_turn(user_id, "assistant", answer)
    await update.message.reply_text(answer)


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN in environment variables.")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(on_menu, pattern=r"^menu$"))
    application.add_handler(CallbackQueryHandler(on_story_selected, pattern=r"^story:"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_chat))

    logger.info("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
