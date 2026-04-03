import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_CHAT_ID = int(os.getenv("OWNER_CHAT_ID", "0"))

# Deadline settings (Moscow time, UTC+3)
DEADLINE_DAY = "saturday"  # Day of the week
DEADLINE_HOUR = 21         # Hour (24h format)
DEADLINE_MINUTE = 0

# Reminder schedule (days before deadline)
REMINDER_DAYS_BEFORE = [2, 1, 0]  # Thursday, Friday, Saturday

# Timezone
TIMEZONE = "Europe/Moscow"
