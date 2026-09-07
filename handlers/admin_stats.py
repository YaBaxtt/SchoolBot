from aiogram import Router, F
from aiogram.types import CallbackQuery

from filters.roles import ADMIN_ROLES, RoleFilter
from keyboards.admin_kb import get_back_to_admin_kb, AdminCB
from database import requests as db

admin_stats_router = Router()
admin_stats_router.callback_query.filter(RoleFilter(ADMIN_ROLES))


@admin_stats_router.callback_query(AdminCB.filter(F.action == "stats"))
async def cb_admin_stats(call: CallbackQuery):
    stats = await db.get_system_stats()
    
    text = (
        f"📊 <b>Общая статистика системы</b>\n\n"
        f"👥 Всего пользователей: <code>{stats['total_users']}</code>\n"
        f" ├ ✅ Активных: <code>{stats['active_users']}</code>\n"
        f" └ ⏳ Ожидают подтверждения: <code>{stats['pending_users']}</code>\n\n"
        f"🎓 Учеников: <code>{stats['students']}</code>\n"
        f"👨‍🏫 Модераторов: <code>{stats['moderators']}</code>\n"
        f"🛡 Администраторов: <code>{stats['admins']}</code>\n"
        f"🏫 Классов: <code>{stats['classes_count']}</code>\n"
        f"📰 Новостей: <code>{stats['news_count']}</code>\n\n"
        f"📩 Жалобы: 🟢 <code>{stats['complaint_new']}</code> | "
        f"🟡 <code>{stats['complaint_in_progress']}</code> | "
        f"🔴 <code>{stats['complaint_closed']}</code>\n"
        f"💡 Предложения: 🟢 <code>{stats['suggestion_new']}</code> | "
        f"🟡 <code>{stats['suggestion_in_progress']}</code> | "
        f"🔴 <code>{stats['suggestion_closed']}</code>"
    )
    
    await call.message.edit_text(text, reply_markup=get_back_to_admin_kb(), parse_mode="HTML")
    await call.answer()
