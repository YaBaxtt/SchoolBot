from datetime import datetime
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import CallbackQuery, Chat, Message, Update, User

from handlers.registration import router as registration_router
from states import RegistrationState


class FirstClickFlowTests(IsolatedAsyncioTestCase):
    async def test_language_callback_is_handled_on_first_click(self) -> None:
        storage = MemoryStorage()
        dispatcher = Dispatcher(storage=storage)
        dispatcher.include_router(registration_router)
        bot = Bot(token="123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi")
        telegram_user = User(id=771, is_bot=False, first_name="New")
        message = Message(
            message_id=1, date=datetime.now(), chat=Chat(id=771, type="private"), from_user=telegram_user, text="/start"
        )
        update = Update(
            update_id=1,
            callback_query=CallbackQuery(
                id="language-first-click", from_user=telegram_user, chat_instance="test", message=message, data="lang_uz"
            ),
        )
        key = StorageKey(bot_id=bot.id, chat_id=telegram_user.id, user_id=telegram_user.id)
        await storage.set_state(key, RegistrationState.language)
        try:
            with patch("aiogram.types.Message.edit_text", AsyncMock()), patch("aiogram.types.CallbackQuery.answer", AsyncMock()):
                await dispatcher.feed_update(bot, update)
            self.assertEqual(await storage.get_state(key), RegistrationState.first_name.state)
            self.assertEqual((await storage.get_data(key))["language"], "uz")
        finally:
            await bot.session.close()
            await storage.close()
