from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database.requests import get_user_by_tg_id
from filters.roles import ADMIN_ROLES, RoleFilter
from permissions import can_view_complaints
from keyboards.admin_kb import AdminCB, get_admin_main_kb, get_back_to_admin_kb, get_settings_kb

admin_main_router = Router()
admin_main_router.message.filter(RoleFilter(ADMIN_ROLES))
admin_main_router.callback_query.filter(RoleFilter(ADMIN_ROLES))


@admin_main_router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    await state.clear()
    user = await get_user_by_tg_id(message.from_user.id)
    await message.answer(
        "🛠 **Панель администратора**\n\nВыберите нужный раздел из меню ниже:",
        reply_markup=get_admin_main_kb(can_view_complaints(user)),
        parse_mode="Markdown"
    )


@admin_main_router.callback_query(AdminCB.filter(F.action == "main"))
async def cb_admin_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    user = await get_user_by_tg_id(call.from_user.id)
    await call.message.edit_text(
        "🛠 **Панель администратора**\n\nВыберите нужный раздел из меню ниже:",
        reply_markup=get_admin_main_kb(can_view_complaints(user)),
        parse_mode="Markdown"
    )


@admin_main_router.callback_query(AdminCB.filter(F.action == "settings"))
async def cb_settings(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    await call.message.edit_text(
        "⚙️ <b>Настройки</b>\n\nВыберите раздел:",
        reply_markup=get_settings_kb(),
        parse_mode="HTML"
    )


@admin_main_router.callback_query(AdminCB.filter(F.action == "help"))
async def cb_admin_help(call: CallbackQuery):
    await call.answer()
    text = (
        "❓ **Справка по админ-панели**\n\n"
        "Администратор может управлять пользователями, заявками, классами, "
        "новостями, обращениями, рассылками и статистикой.\n\n"
        "SuperAdmin дополнительно может назначать администраторов."
    )
    await call.message.edit_text(text, reply_markup=get_back_to_admin_kb(), parse_mode="Markdown")
