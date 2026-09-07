from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser
from database.requests import get_user_by_tg_id

class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        event_user: TgUser = data.get("event_from_user")
        
        # The same outer middleware runs for Message and CallbackQuery events.
        # Registration remains responsible for creating users; this only loads
        # an existing account and always exposes the dependency to handlers.
        user = await get_user_by_tg_id(event_user.id) if event_user else None
        data["current_user"] = user

        return await handler(event, data)
