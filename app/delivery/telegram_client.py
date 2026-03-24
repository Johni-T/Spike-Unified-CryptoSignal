import logging

from telegram import Bot
from telegram.constants import ParseMode

from app.config import settings


logger = logging.getLogger(__name__)


class TelegramDelivery:
    def __init__(self) -> None:
        self.bot = Bot(settings.telegram_token)

    async def send_photo(self, chart_buffer, caption: str) -> int | None:
        if not settings.telegram_chat_id:
            logger.warning("TELEGRAM_CHAT_ID is empty, skip send_photo")
            return None
        message = await self.bot.send_photo(
            chat_id=settings.telegram_chat_id,
            photo=chart_buffer,
            caption=caption,
            parse_mode=ParseMode.HTML,
        )
        return message.message_id

    async def edit_caption(self, message_id: int | None, caption: str) -> None:
        if not message_id or not settings.telegram_chat_id:
            return
        await self.bot.edit_message_caption(
            chat_id=settings.telegram_chat_id,
            message_id=message_id,
            caption=caption,
            parse_mode=ParseMode.HTML,
        )
