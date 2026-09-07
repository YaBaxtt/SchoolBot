import os
from pathlib import Path

from dotenv import load_dotenv


# Load the project's .env even if ``bot.py`` was started from another folder.
load_dotenv(Path(__file__).resolve().with_name(".env"))


ADMIN_IDS: list[int] = [
    8671852462,
]


BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is required")


def optional_chat_id(env_name: str) -> int | None:
    value = os.getenv(env_name)

    if value and value.lstrip("-").isdigit():
        return int(value)

    return None


# Preferred explicit name; the legacy name remains a compatibility fallback.
REGISTRATION_REVIEW_CHAT_ID = (
    optional_chat_id("REGISTRATION_REVIEW_CHAT_ID") or optional_chat_id("REGISTRATION_GROUP_ID")
)
REGISTRATION_GROUP_ID = REGISTRATION_REVIEW_CHAT_ID
FEEDBACK_GROUP_ID = optional_chat_id("FEEDBACK_GROUP_ID")
