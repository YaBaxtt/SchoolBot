import asyncio
import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest, TelegramRetryAfter

from filters.roles import ADMIN_ROLES, RoleFilter
from keyboards.admin_kb import (
    AdminCB, 
    get_broadcast_confirm_kb, 
    get_back_to_admin_kb
)
from database import requests as db
from states.feedback import BroadcastState

admin_broadcast_router = Router()
admin_broadcast_router.callback_query.filter(RoleFilter(ADMIN_ROLES))
admin_broadcast_router.message.filter(RoleFilter(ADMIN_ROLES))

logger = logging.getLogger(__name__)


# --- Шаг 1: Нажатие на кнопку "Рассылка" ---

@admin_broadcast_router.callback_query(AdminCB.filter(F.action == "broadcast"))
async def cb_start_broadcast(call: CallbackQuery, state: FSMContext):
    await state.set_state(BroadcastState.waiting_for_text)
    await call.message.answer(
        "📢 <b>Массовая рассылка сообщений</b>\n\n"
        "Введите текст сообщения, которое получат все зарегистрированные пользователи.\n"
        "<i>Поддерживается HTML-разметка (<b>жирный</b>, <i>курсив</i>, <code>код</code>).</i>",
        reply_markup=get_back_to_admin_kb(),
        parse_mode="HTML"
    )
    await call.answer()


# --- Шаг 2: Ввод текста рассылки и Предпросмотр ---

@admin_broadcast_router.message(BroadcastState.waiting_for_text)
async def process_broadcast_text(message: Message, state: FSMContext):
    broadcast_text = (message.text or "").strip()
    if not broadcast_text:
        await message.answer("⚠️ Текст рассылки не может быть пустым.")
        return
    await state.update_data(broadcast_text=broadcast_text)
    await state.set_state(BroadcastState.waiting_for_confirm)

    preview_msg = (
        "👀 <b>ПРЕДПРОСМОТР СООБЩЕНИЯ:</b>\n"
        "─────────────────────────\n\n"
        f"{broadcast_text}\n\n"
        "─────────────────────────\n"
        "Вы уверены, что хотите отправить это сообщение всем пользователям?"
    )

    await message.answer(
        preview_msg,
        reply_markup=get_broadcast_confirm_kb(),
        parse_mode="HTML"
    )


# --- Шаг 3: Отмена рассылки ---

@admin_broadcast_router.callback_query(BroadcastState.waiting_for_confirm, AdminCB.filter(F.action == "broadcast_cancel"))
async def cb_cancel_broadcast(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "❌ <b>Рассылка отменена.</b>",
        reply_markup=get_back_to_admin_kb(),
        parse_mode="HTML"
    )
    await call.answer()


# --- Шаг 4: Подтверждение и запуск рассылки ---

@admin_broadcast_router.callback_query(BroadcastState.waiting_for_confirm, AdminCB.filter(F.action == "broadcast_confirm"))
async def cb_confirm_broadcast(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    broadcast_text = data.get("broadcast_text")

    if not broadcast_text:
        await call.answer("Ошибка: текст рассылки не найден.", show_alert=True)
        await state.clear()
        return

    await state.clear()
    users = await db.get_active_users()
    total_users = len(users)

    if total_users == 0:
        await call.message.edit_text("👥 Нет активных пользователей для рассылки.")
        await call.answer()
        return

    status_message = await call.message.edit_text(
        f"⏳ <b>Рассылка запущена...</b>\n"
        f"Обработано: 0 / {total_users}",
        parse_mode="HTML"
    )

    success_count = 0
    error_count = 0

    for index, user in enumerate(users, start=1):
        try:
            await bot.send_message(
                chat_id=user.telegram_id,
                text=broadcast_text,
                parse_mode="HTML"
            )
            success_count += 1
        except TelegramForbiddenError:
            # Пользователь заблокировал бота
            error_count += 1
        except TelegramBadRequest as e:
            # Неверный ID или пользователь удален
            logger.warning(f"Ошибка отправки пользователю {user.telegram_id}: {e}")
            error_count += 1
        except TelegramRetryAfter as e:
            # Превышен лимит запросов Telegram — ждем и пробуем снова
            await asyncio.sleep(e.retry_after)
            try:
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=broadcast_text,
                    parse_mode="HTML"
                )
                success_count += 1
            except Exception:
                error_count += 1
        except Exception as e:
            logger.error(f"Неизвестная ошибка при рассылке {user.telegram_id}: {e}")
            error_count += 1

        # Задержка 50мс между отправками для соблюдения лимитов Telegram (30 msg/sec)
        await asyncio.sleep(0.05)

    # Формируем итоговый отчет
    report_text = (
        "📊 <b>РАССЫЛКА ЗАВЕРШЕНА</b>\n\n"
        f"✅ <b>Успешно отправлено:</b> {success_count}\n"
        f"❌ <b>Ошибок:</b> {error_count}\n"
        f"👥 <b>Всего пользователей:</b> {total_users}"
    )

    await status_message.edit_text(
        report_text,
        reply_markup=get_back_to_admin_kb(),
        parse_mode="HTML"
    )
    await call.answer()


router = admin_broadcast_router
