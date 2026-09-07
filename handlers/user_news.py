from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import get_news_by_id, get_news_count, get_news_list, get_user_by_tg_id
from filters import RegisteredUserFilter
from keyboards import get_back_to_news_kb, get_main_menu_kb, get_news_list_kb
from locales.texts import TEXTS

router = Router()
router.message.filter(RegisteredUserFilter())
router.callback_query.filter(RegisteredUserFilter())
PER_PAGE = 5
NEWS_BUTTONS = {texts["btn_news"] for texts in TEXTS.values()}


@router.message(F.text.in_(NEWS_BUTTONS))
@router.message(Command("news"))
async def show_news_list_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = await get_user_by_tg_id(message.from_user.id)
    lang = user.language if user else "ru"
    lang_texts = TEXTS.get(lang, TEXTS["ru"])

    total_count = await get_news_count()
    if total_count == 0:
        await message.answer(
            lang_texts["no_news"],
            reply_markup=get_back_to_news_kb(lang=lang),
            parse_mode="HTML",
        )
        return

    news_items = await get_news_list(limit=PER_PAGE, offset=0)
    kb = get_news_list_kb(news_items, page=0, total_count=total_count, per_page=PER_PAGE, lang=lang)

    await message.answer(lang_texts["news_list_title"], reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("news_page_"))
async def process_news_pagination(callback: CallbackQuery) -> None:
    try:
        page = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer()
        return

    user = await get_user_by_tg_id(callback.from_user.id)
    lang = user.language if user else "ru"
    lang_texts = TEXTS.get(lang, TEXTS["ru"])

    total_count = await get_news_count()
    max_page = max((total_count - 1) // PER_PAGE, 0)
    page = min(max(page, 0), max_page)
    offset = page * PER_PAGE
    news_items = await get_news_list(limit=PER_PAGE, offset=offset)

    kb = get_news_list_kb(news_items, page=page, total_count=total_count, per_page=PER_PAGE, lang=lang)

    await callback.message.edit_text(lang_texts["news_list_title"], reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("view_news_"))
async def process_view_news(callback: CallbackQuery) -> None:
    parts = callback.data.split("_")
    try:
        news_id = int(parts[2])
        page = int(parts[3])
    except (IndexError, ValueError):
        await callback.answer()
        return

    user = await get_user_by_tg_id(callback.from_user.id)
    lang = user.language if user else "ru"
    lang_texts = TEXTS.get(lang, TEXTS["ru"])

    news_item = await get_news_by_id(news_id)
    if not news_item:
        await callback.answer(lang_texts["no_news"], show_alert=True)
        return

    date_str = news_item.created_at.strftime("%d.%m.%Y %H:%M")
    text = lang_texts["news_format"].format(
        title=escape(news_item.title),
        date=date_str,
        content=escape(news_item.content)
    )

    kb = get_back_to_news_kb(page=page, lang=lang)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "news_main_menu")
async def return_to_main_menu(callback: CallbackQuery) -> None:
    user = await get_user_by_tg_id(callback.from_user.id)
    if not user:
        await callback.answer()
        return

    lang = user.language or "ru"
    lang_texts = TEXTS.get(lang, TEXTS["ru"])
    await callback.message.edit_text(lang_texts["menu_returned"])
    await callback.message.answer(
        lang_texts["main_menu"], reply_markup=get_main_menu_kb(lang)
    )
    await callback.answer()
