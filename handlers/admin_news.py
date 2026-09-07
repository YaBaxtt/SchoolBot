from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import requests as db
from filters.roles import ADMIN_ROLES, RoleFilter
from keyboards.admin_kb import AdminCB, get_back_to_admin_kb, get_news_kb, get_news_publish_kb
from states.admin_news import CreateNewsState

admin_news_router = Router()
admin_news_router.callback_query.filter(RoleFilter(ADMIN_ROLES))
admin_news_router.message.filter(RoleFilter(ADMIN_ROLES))


@admin_news_router.callback_query(AdminCB.filter(F.action == "news"))
async def cb_admin_news(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.message.edit_text(
        "📰 <b>Новости</b>\n\nВыберите действие:", reply_markup=get_news_kb(), parse_mode="HTML"
    )
    await call.answer()


@admin_news_router.callback_query(AdminCB.filter(F.action == "news_list"))
async def cb_news_list(call: CallbackQuery) -> None:
    news_list = await db.get_recent_news(limit=10)
    text = "📋 <b>Последние новости</b>\n\n"
    if not news_list:
        text += "Новости пока не опубликованы."
    else:
        for item in news_list:
            date = item.created_at.strftime("%d.%m.%Y") if item.created_at else "—"
            text += f"📰 <b>{escape(item.title)}</b>\n{escape(item.content[:180])}\n📅 {date}\n───────────────\n"
    await call.message.edit_text(text, reply_markup=get_news_kb(), parse_mode="HTML")
    await call.answer()


@admin_news_router.callback_query(AdminCB.filter(F.action == "news_create"))
async def cb_news_create(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(CreateNewsState.waiting_for_title)
    await call.message.edit_text(
        "➕ <b>Создание новости</b>\n\nВведите заголовок новости:",
        reply_markup=get_back_to_admin_kb(),
        parse_mode="HTML",
    )
    await call.answer()


@admin_news_router.message(CreateNewsState.waiting_for_title)
async def process_news_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer("⚠️ Заголовок не может быть пустым.")
        return
    await state.update_data(news_title=title)
    await state.set_state(CreateNewsState.waiting_for_content)
    await message.answer("📝 Введите текст новости:", reply_markup=get_back_to_admin_kb())


@admin_news_router.message(CreateNewsState.waiting_for_content)
async def process_news_content(message: Message, state: FSMContext) -> None:
    content = (message.text or "").strip()
    if not content:
        await message.answer("⚠️ Текст новости не может быть пустым.")
        return
    data = await state.get_data()
    title = data.get("news_title", "")
    await state.update_data(news_content=content)
    await state.set_state(CreateNewsState.waiting_for_confirm)
    await message.answer(
        "👀 <b>Предпросмотр новости</b>\n\n"
        f"📰 <b>{escape(title)}</b>\n\n{escape(content)}\n\nОпубликовать?",
        reply_markup=get_news_publish_kb(),
        parse_mode="HTML",
    )


@admin_news_router.callback_query(CreateNewsState.waiting_for_confirm, AdminCB.filter(F.action == "news_cancel"))
async def cb_news_cancel(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.message.edit_text("❌ Создание новости отменено.", reply_markup=get_news_kb())
    await call.answer()


@admin_news_router.callback_query(CreateNewsState.waiting_for_confirm, AdminCB.filter(F.action == "news_publish"))
async def cb_news_publish(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    title = data.get("news_title")
    content = data.get("news_content")
    author = await db.get_user_by_tg_id(call.from_user.id)
    if not title or not content or not author:
        await state.clear()
        await call.message.edit_text("⚠️ Не удалось найти данные новости.", reply_markup=get_news_kb())
        await call.answer()
        return
    await db.create_news(title=title, content=content, author_db_id=author.id)
    await state.clear()
    await call.message.edit_text(
        "✅ <b>Новость опубликована!</b>", reply_markup=get_news_kb(), parse_mode="HTML"
    )
    await call.answer()
