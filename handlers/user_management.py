from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import get_all_users, get_user_by_tg_id, update_user_role
from filters import RegisteredUserFilter
from filters.roles import ADMIN_ROLES, SUPERADMIN_ROLES, RoleFilter, normalize_role
from permissions import ASSIGNABLE_ROLES, UserRole, can_access_admin, can_access_staff
from handlers.profile import render_profile_text
from keyboards import get_help_back_kb, get_main_menu_kb, get_profile_main_kb
from locales.texts import TEXTS

router = Router()
router.message.filter(RegisteredUserFilter())
router.callback_query.filter(RegisteredUserFilter())

VALID_ROLES = ASSIGNABLE_ROLES
HELP_BUTTONS = {texts["btn_help"] for texts in TEXTS.values()}


def get_role_display_name(role: str, lang: str = "ru") -> str:
    lang_texts = TEXTS.get(lang, TEXTS["ru"])
    key = f"role_{role}"
    return lang_texts.get(key, role)


# --- Команда /me (Доступна всем зарегистрированным) ---

@router.message(Command("me"))
async def cmd_me(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = await get_user_by_tg_id(message.from_user.id)
    if not user:
        return

    lang = user.language or "ru"
    await message.answer(
        render_profile_text(user),
        reply_markup=get_profile_main_kb(lang),
        parse_mode="HTML",
    )


@router.message(F.text.in_(HELP_BUTTONS))
@router.message(Command("help"))
async def show_help(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = await get_user_by_tg_id(message.from_user.id)
    if not user:
        return
    lang = user.language or "ru"
    help_text = TEXTS[lang]["help_text"]
    if can_access_staff(user):
        help_text += TEXTS[lang]["help_staff"]
    if can_access_admin(user):
        help_text += TEXTS[lang]["help_admin"]
    await message.answer(help_text, reply_markup=get_help_back_kb(lang), parse_mode="HTML")


@router.callback_query(F.data == "help_main_menu")
async def help_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user = await get_user_by_tg_id(callback.from_user.id)
    if not user:
        await callback.answer()
        return
    lang = user.language or "ru"
    await callback.message.edit_text(TEXTS[lang]["menu_returned"])
    await callback.message.answer(TEXTS[lang]["main_menu"], reply_markup=get_main_menu_kb(lang))
    await callback.answer()


# --- Команда /users (Доступна только admin и superadmin) ---

@router.message(Command("users"), RoleFilter(ADMIN_ROLES))
async def cmd_users(message: Message) -> None:
    current_user = await get_user_by_tg_id(message.from_user.id)
    lang = current_user.language if current_user else "ru"
    lang_texts = TEXTS.get(lang, TEXTS["ru"])

    users = await get_all_users()
    if not users:
        await message.answer(lang_texts["no_users"])
        return

    response = [lang_texts["users_list_title"]]

    for u in users:
        role_str = get_role_display_name(u.role, lang)
        item = lang_texts["user_item_format"].format(
            id=u.id,
            telegram_id=u.telegram_id,
            first_name=u.first_name,
            last_name=u.last_name,
            class_name=u.class_name,
            role=role_str
        )
        response.append(item)

    await message.answer("\n".join(response), parse_mode="HTML")


# --- Команда /role (Доступна только superadmin) ---

@router.message(Command("role"), RoleFilter(SUPERADMIN_ROLES))
async def cmd_set_role(message: Message) -> None:
    current_user = await get_user_by_tg_id(message.from_user.id)
    lang = current_user.language if current_user else "ru"
    lang_texts = TEXTS.get(lang, TEXTS["ru"])

    # Формат команды: /role 123456789 admin
    args = message.text.split()
    if len(args) != 3:
        await message.answer(lang_texts["invalid_role_cmd"], parse_mode="HTML")
        return

    target_tg_id_str, new_role = args[1], args[2].lower()

    if not target_tg_id_str.isdigit():
        await message.answer(lang_texts["invalid_role_cmd"], parse_mode="HTML")
        return

    target_tg_id = int(target_tg_id_str)

    if new_role not in VALID_ROLES:
        await message.answer(lang_texts["invalid_role_name"])
        return

    target_user = await get_user_by_tg_id(target_tg_id)
    if not target_user:
        await message.answer(lang_texts["user_not_found"])
        return

    if normalize_role(target_user.role) == UserRole.SUPERADMIN.value:
        await message.answer("❌ Роль SuperAdmin нельзя изменить этой командой.")
        return

    await update_user_role(target_tg_id, new_role)
    role_str = get_role_display_name(new_role, lang)

    await message.answer(
        lang_texts["role_updated_success"].format(
            telegram_id=target_tg_id,
            role=role_str
        ),
        parse_mode="HTML"
    )
