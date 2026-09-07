TEXTS = {
    "ru": {
        "select_lang": "Выберите язык / Tilni tanlang:",
        "ask_first_name": "Введите ваше имя:",
        "ask_last_name": "Введите вашу фамилию:",
        "confirm_full_name": "Проверьте данные:\n\nИмя: {first_name}\nФамилия: {last_name}\n\nВсё верно?",
        "btn_confirm_name": "✅ Всё верно",
        "btn_edit_name": "✏️ Исправить имя",
        "ask_class": "Введите ваш класс (например, 10-А):",
        "ask_grade": "🎓 Выберите параллель:",
        "ask_class_from_list": "🏫 Выберите класс:",
        "no_school_classes": "⚠️ Классы школы пока не настроены.\n\nПожалуйста, обратитесь к администрации.",
        "class_choice_invalid": "⚠️ Этот класс больше недоступен. Выберите класс из списка.",
        "reg_complete": "✅ Регистрация успешно завершена!",
        "registration_submitted": "⏳ Ваша заявка отправлена администрации.",
        "registration_pending": "⏳ Ваша заявка уже отправлена и ожидает подтверждения администрации.",
        "registration_rejected": "❌ Ваша заявка на регистрацию отклонена. Обратитесь к администрации.",
        "registration_approved": "✅ Ваша регистрация подтверждена администрацией.\n\nТеперь вам доступен School Bot.",
        "main_menu": "Выберите нужный раздел:",
        "btn_news": "📰 Новости",
        "btn_schedule": "📅 Расписание",
        "btn_events": "🎯 Мероприятия",
        "btn_achievements": "🏆 Достижения",
        "btn_requests": "📨 Обращения",
        "btn_polls": "📊 Опросы",
        "btn_games": "🎮 Игры",
        "btn_my_class": "👥 Мой класс",
        "btn_complaint": "📩 Жалоба",
        "btn_suggestion": "💡 Предложение",
        "btn_question": "❓ Вопрос / просьба",
        "btn_my_feedbacks": "📨 Мои обращения",
        "btn_profile": "👤 Профиль",
        "btn_help": "🆘 Помощь",
        "welcome_back": "👋 С возвращением, {first_name}!",
        "btn_back_to_menu": "⬅️ Главное меню",
        "btn_back": "⬅️ Назад",
        "menu_returned": "Главное меню снова доступно ниже.",
        "value_required": "⚠️ Пожалуйста, отправьте непустой текст.",
        "callback_expired": "⚠️ Эта кнопка устарела. Откройте раздел заново.",

        # Роли
        "role_student": "Ученик",
        "role_moderator": "Модератор",
        "role_admin": "Администратор",
        "role_superadmin": "Суперадмин",

        # Ошибки доступа
        "access_denied": "❌ У вас нет доступа к этой команде.",
        "invalid_role_cmd": "⚠️ Неверный формат команды.\nИспользование: <code>/role TELEGRAM_ID РОЛЬ</code>\nДопустимые роли: student, moderator, admin",
        "invalid_role_name": "❌ Неверное имя роли. Допустимые: student, moderator, admin",
        "user_not_found": "❌ Пользователь с таким Telegram ID не найден.",
        "role_updated_success": "✅ Роль пользователя {telegram_id} успешно изменена на <b>{role}</b>.",

        # Информация о пользователе (/me)
        "me_info": (
            "👤 <b>Ваша информация (/me)</b>\n\n"
            "<b>Telegram ID:</b> <code>{telegram_id}</code>\n"
            "<b>Имя:</b> {first_name}\n"
            "<b>Фамилия:</b> {last_name}\n"
            "<b>Класс:</b> {class_name}\n"
            "<b>Роль:</b> {role}"
        ),

        # Список пользователей (/users)
        "users_list_title": "👥 <b>Список зарегистрированных пользователей:</b>\n",
        "no_users": "Пользователи не найдены.",
        "user_item_format": (
            "<b>ID:</b> {id} | <b>TG ID:</b> <code>{telegram_id}</code>\n"
            "<b>ФИО:</b> {first_name} {last_name}\n"
            "<b>Класс:</b> {class_name} | <b>Роль:</b> {role}\n"
            "───────────────"
        ),

        # Новости
        "news_list_title": "📰 <b>Последние новости:</b>",
        "no_news": "📰 <b>Новости</b>\n\nПока новых школьных новостей нет.",
        "btn_back_to_list": "⬅️ Назад к новостям",
        "btn_next_page": "Далее ➡️",
        "btn_prev_page": "⬅️ Назад",
        "news_format": "📰 <b>{title}</b>\n\n📅 <i>{date}</i>\n\n{content}",

        # Обращения
        "ask_complaint": "📩 <b>Новая жалоба</b>\n\nОпишите проблему одним сообщением.",
        "ask_suggestion": "💡 <b>Новое предложение</b>\n\nНапишите вашу идею или предложение для школы.",
        "ask_question": "❓ <b>Вопрос или просьба</b>\n\nОпишите, с чем вам нужна помощь, одним сообщением.",
        "complaint_warning": (
            "⚠️ <b>Перед отправкой жалобы</b>\n\n"
            "Обращение предназначено для реальных школьных проблем.\n\n"
            "Не используйте:\n• оскорбления;\n• угрозы;\n• неприемлемый или сексуальный контент;\n• спам;\n• бессмысленные тестовые сообщения.\n\n"
            "Обращение технически связано с вашим аккаунтом. При серьёзном нарушении правил администрация сможет определить автора.\n\n"
            "Используйте систему ответственно."
        ),
        "suggestion_warning": (
            "💡 <b>Перед отправкой предложения</b>\n\n"
            "Предложения предназначены для полезных идей по улучшению школы.\n\n"
            "Не отправляйте:\n• спам;\n• оскорбления;\n• бессмысленные сообщения;\n• неприемлемый контент.\n\n"
            "Сообщение технически связано с аккаунтом автора. При злоупотреблении администрация может определить отправителя."
        ),
        "btn_complaint_continue": "✅ Я понимаю",
        "btn_suggestion_continue": "✅ Продолжить",
        "feedback_warning_waiting": "Выберите «Продолжить» или «Отмена» под сообщением.",
        "feedback_warning_accepted": "✅ Принято. Теперь опишите обращение одним сообщением.",
        "confirm_feedback": "Отправить сообщение администрации?\n\n<b>Текст:</b>\n{text}",
        "btn_confirm_yes": "✅ Отправить",
        "btn_confirm_no": "❌ Отмена",
        "btn_cancel": "❌ Отмена",
        "feedback_sent": "✅ Ваше обращение отправлено администрации.",
        "feedback_cancelled": "Отправка обращения отменена.",
        "feedback_waiting_confirmation": "Выберите «Отправить» или «Отмена» под сообщением.",
        "my_feedbacks_title": "📨 <b>Мои обращения</b>",
        "no_my_feedbacks": "📨 <b>Мои обращения</b>\n\nВы ещё не отправляли обращений.",
        "my_feedback_item": "{type} #{id} — {status}",
        "my_feedback_detail": "{type} #{id}\n\n📅 Дата: {date}\n📌 Статус: {status}\n\n<b>Текст:</b>\n{text}",
        "btn_back_to_feedbacks": "⬅️ К моим обращениям",
        "help_text": (
            "📚 <b>Что умеет школьный бот?</b>\n\n"
            "📰 /news — новости\n📅 /schedule — расписание\n🎯 /events — мероприятия\n🏆 /achievements — достижения\n"
            "🎮 /games — упражнения на память и логику\n👥 /class — мой класс\n📨 обращения — связь со школой\n"
            "👤 /profile — профиль\n❓ /help — справка"
        ),
        "help_staff": "\n\n👨‍🏫 <b>Сотруднику</b>\n/staff — мои классы, ученики, заявки, объявления, расписание и статистика.",
        "help_admin": "\n\n🛠 <b>Администратору</b>\n/admin — пользователи, классы, новости, обращения, рассылка и настройки.",
        "type_complaint": "📩 Жалоба",
        "type_suggestion": "💡 Предложение",
        "type_question": "❓ Вопрос / просьба",
        "status_new": "Новое",
        "status_in_progress": "В работе",
        "status_closed": "Закрыто",
        "admin_feedback_notification": (
            "📩 <b>Новое обращение!</b>\n\n"
            "<b>Тип:</b> {type}\n"
            "<b>Имя:</b> {first_name}\n"
            "<b>Фамилия:</b> {last_name}\n"
            "<b>Класс:</b> {class_name}\n"
            "<b>Дата:</b> {date}\n\n"
            "<b>Текст:</b>\n{text}"
        ),
        "admin_feedbacks_title": "📋 <b>Последние обращения:</b>\n",
        "no_feedbacks": "Обращений пока нет.",
        "feedback_item_format": (
            "<b>#{id} [{type}]</b> — Status: <i>{status}</i>\n"
            "<b>От:</b> {first_name} {last_name} ({class_name})\n"
            "<b>Дата:</b> {date}\n"
            "<b>Текст:</b> {text}\n"
            "───────────────"
        ),

        # Профиль
        "lang_name_ru": "Русский",
        "lang_name_uz": "O'zbekcha",
        "profile_card": (
            "👤 <b>Мой профиль</b>\n\n"
            "👨 Имя: {first_name}\n"
            "👨 Фамилия: {last_name}\n"
            "🏫 Класс: {class_name}\n"
            "🌐 Язык: {language}\n"
            "🎓 Роль: {role}\n"
            "🆔 Код: <code>{user_code}</code>\n"
            "📅 Регистрация: {created_at}"
        ),
        "btn_edit_profile": "✏️ Редактировать профиль",
        "btn_edit_first_name": "Имя",
        "btn_edit_last_name": "Фамилия",
        "btn_edit_class": "Класс",
        "btn_edit_language": "Язык",
        "btn_change_class_request": "🔄 Запросить смену класса",
        "btn_public_profile_enable": "🔗 Показывать ссылку в рейтинге",
        "btn_public_profile_disable": "🔒 Не показывать ссылку в рейтинге",
        "public_profile_enabled": "Ссылка на Telegram в рейтинге включена, если у вас указан username.",
        "public_profile_disabled": "Ссылка на Telegram в рейтинге скрыта.",
        "class_change_title": "🔄 <b>Смена класса</b>\n\nВыберите новую параллель:",
        "class_change_choose_class": "🔄 <b>Смена класса</b>\n\nВыберите новый класс:",
        "class_change_reason": "Напишите причину перевода одним сообщением или пропустите этот шаг.",
        "class_change_skip_reason": "Пропустить причину",
        "class_change_confirm": "Текущий класс: <b>{old_class}</b>\nНовый класс: <b>{new_class}</b>\nПричина: {reason}\n\nОтправить заявку?",
        "class_change_submit": "✅ Отправить заявку",
        "class_change_submitted": "✅ Заявка на смену класса отправлена. Ваш класс изменится только после одобрения администрации.",
        "class_change_pending": "⏳ У вас уже есть заявка на смену класса, ожидающая рассмотрения.",
        "class_change_same": "Вы уже учитесь в этом классе.",
        "class_change_use_request": "Этот экран обновлён. Откройте профиль и отправьте заявку на смену класса.",
        "btn_cancel_edit": "⬅️ Назад",
        "edit_menu_title": "✏️ <b>Редактирование профиля</b>\n\nВыберите поле, которое хотите изменить.",
        "ask_new_first_name": "Введите новое имя:",
        "ask_new_last_name": "Введите новую фамилию:",
        "ask_new_class": "Введите новый класс:",
        "ask_new_language": "Выберите язык:",
        "profile_updated": "✅ Профиль обновлён."
        ,"schedule_title": "📅 <b>Расписание</b>\n🏫 {class_name}\n\nВыберите день:",
        "schedule_empty": "На этот день уроков пока нет.",
        "schedule_day": "📅 <b>{day}</b>\n🏫 {class_name}\n\n{lessons}",
        "events_title": "🎯 <b>Ближайшие мероприятия</b>",
        "events_empty": "Ближайших мероприятий пока нет.",
        "achievements_title": "🏆 <b>Достижения школы</b>",
        "achievements_empty": "Опубликованных достижений пока нет.",
        "polls_title": "📊 <b>Опросы</b>",
        "polls_empty": "Активных опросов пока нет.",
        "vote_saved": "✅ Голос принят.",
        "vote_unavailable": "Этот опрос уже закрыт или вы уже голосовали.",
        "requests_title": "📨 <b>Обращения</b>\n\nВыберите действие:",
        "my_class_title": "👥 <b>Мой класс: {class_name}</b>\n\nУчеников: {students}\n\n<b>Сегодня:</b>\n{lessons}\n\n<b>Последние объявления:</b>\n{announcements}",
        "no_announcements": "Пока нет.",
        "btn_back_to_sections": "⬅️ К разделам",
        "games_home": "🧠 <b>Игры для интеллекта</b>\n\nНебольшие упражнения на память, внимание и логику.\n\nНе проводите здесь слишком много времени — учёба и отдых важнее рекордов 🙂",
        "game_memory": "🧠 Память чисел",
        "game_logic": "🔢 Логическая цепочка",
        "game_stats": "🏆 Статистика",
        "game_play": "▶️ Играть",
        "game_back": "⬅️ Назад",
        "memory_intro": "🧠 <b>Память чисел</b>\n\nЗапоминайте числа и затем нажимайте их в точном порядке.",
        "memory_level": "🧠 <b>Уровень {level}</b>\n\nЗапомните числа и их порядок.",
        "memory_numbers": "🧠 <b>Уровень {level}</b>\n\n<b>{sequence}</b>\n\nЗапоминайте…",
        "memory_answer": "🧠 <b>Уровень {level}</b>\n\nНажимайте числа в правильном порядке.",
        "memory_next_number": "🧠 <b>Уровень {level}</b>\n\nВерно. Выберите следующее число.",
        "memory_level_complete": "✅ Уровень {level} пройден. Следующий уровень…",
        "memory_error": "❌ <b>Ошибка</b>\n\nПравильная последовательность: <b>{sequence}</b>\nСчёт: <b>{score}</b>",
        "memory_complete": "🏁 <b>Память чисел завершена!</b>\n\nПройденный уровень: <b>{level}</b>\nСчёт: <b>{score}</b>",
        "game_retry": "🔁 Ещё раз",
        "logic_intro": "🔢 <b>Логическая цепочка</b>\n\nРешите 5 коротких задач на закономерности.",
        "logic_question": "🔢 <b>Логическая цепочка</b>\nВопрос {round}/5\n\n<b>{sequence}</b>",
        "logic_correct": "✅ Верно!\n\n{explanation}",
        "logic_wrong": "❌ Неверно. Правильный ответ: <b>{correct}</b>\n\n{explanation}",
        "logic_next": "➡️ Следующий вопрос",
        "logic_complete": "🏁 <b>Логическая цепочка завершена!</b>\n\nВерных ответов: <b>{correct}/5</b>\nСчёт: <b>{score}</b>",
        "logic_rule_add": "+{value} на каждом шаге.",
        "logic_rule_multiply": "×{value} на каждом шаге.",
        "logic_rule_alternate": "+3, −1, +3, −1…",
        "logic_rule_interleaved": "Две чередующиеся последовательности.",
        "game_personal_stats": "🏆 <b>Игровая статистика</b>\n\n🧠 Память чисел\nЛучший уровень: <b>{memory_level}</b>\nЛучший счёт: <b>{memory_score}</b>\nИгр: <b>{memory_games}</b>\n\n🔢 Логическая цепочка\nЛучший счёт: <b>{logic_score}</b>\nЛучший результат: <b>{logic_correct}</b>\nИгр: <b>{logic_games}</b>",
        "game_leaderboard": "🏆 <b>{title}</b>\n\n{rows}",
        "game_leaderboard_empty": "Результатов пока нет."
        ,"leaderboard_week": "за неделю"
        ,"leaderboard_all": "за всё время"
        ,"leaderboard_prize_default": "🎁 <b>Награды недели</b>\n\nИногда создатель бота награждает лидеров рейтинга Telegram-подарками. Следите за таблицей — приз может достаться вам."
    },
    "uz": {
        "select_lang": "Tilni tanlang / Выберите язык:",
        "ask_first_name": "Ismingizni kiriting:",
        "ask_last_name": "Familiyangizni kiriting:",
        "confirm_full_name": "Ma'lumotlarni tekshiring:\n\nIsm: {first_name}\nFamiliya: {last_name}\n\nHammasi to'g'rimi?",
        "btn_confirm_name": "✅ Hammasi to'g'ri",
        "btn_edit_name": "✏️ Ismni tuzatish",
        "ask_class": "Sinfingizni kiriting (masalan, 10-A):",
        "ask_grade": "🎓 Parallelni tanlang:",
        "ask_class_from_list": "🏫 Sinfni tanlang:",
        "no_school_classes": "⚠️ Maktab sinflari hali sozlanmagan.\n\nIltimos, ma'muriyatga murojaat qiling.",
        "class_choice_invalid": "⚠️ Bu sinf endi mavjud emas. Ro'yxatdan sinfni tanlang.",
        "reg_complete": "✅ Ro'yxatdan o'tish muvaffaqiyatli yakunlandi!",
        "registration_submitted": "⏳ Arizangiz ma'muriyatga yuborildi.",
        "registration_pending": "⏳ Arizangiz yuborilgan va ma'muriyat tasdig'ini kutmoqda.",
        "registration_rejected": "❌ Ro'yxatdan o'tish arizangiz rad etildi. Ma'muriyatga murojaat qiling.",
        "registration_approved": "✅ Ro'yxatdan o'tishingiz ma'muriyat tomonidan tasdiqlandi.\n\nEndi School Bot sizga ochiq.",
        "main_menu": "Kerakli bo'limni tanlang:",
        "btn_news": "📰 Yangiliklar",
        "btn_schedule": "📅 Dars jadvali",
        "btn_events": "🎯 Tadbirlar",
        "btn_achievements": "🏆 Yutuqlar",
        "btn_requests": "📨 Murojaatlar",
        "btn_polls": "📊 So'rovlar",
        "btn_games": "🎮 O'yinlar",
        "btn_my_class": "👥 Mening sinfim",
        "btn_complaint": "📩 Shikoyat",
        "btn_suggestion": "💡 Taklif",
        "btn_question": "❓ Savol / iltimos",
        "btn_my_feedbacks": "📨 Mening murojaatlarim",
        "btn_profile": "👤 Profil",
        "btn_help": "🆘 Yordam",
        "welcome_back": "👋 Qaytganingiz bilan, {first_name}!",
        "btn_back_to_menu": "⬅️ Asosiy menyu",
        "btn_back": "⬅️ Ortga",
        "menu_returned": "Asosiy menyu quyida yana mavjud.",
        "value_required": "⚠️ Iltimos, bo'sh bo'lmagan matn yuboring.",
        "callback_expired": "⚠️ Bu tugma eskirgan. Bo'limni qayta oching.",

        # Роли
        "role_student": "O'quvchi",
        "role_moderator": "Moderator",
        "role_admin": "Administrator",
        "role_superadmin": "Superadmin",

        # Ошибки доступа
        "access_denied": "❌ Sizda bu buyruqdan foydalanish huquqi yo'q.",
        "invalid_role_cmd": "⚠️ Buyruq formati noto'g'ri.\nFoydalanish: <code>/role TELEGRAM_ID ROL</code>\nRuxsat berilgan hollar: student, moderator, admin",
        "invalid_role_name": "❌ Rol nomi noto'g'ri. Ruxsat berilganlar: student, moderator, admin",
        "user_not_found": "❌ Ushbu Telegram ID ga ega foydalanuvchi topilmadi.",
        "role_updated_success": "✅ Foydalanuvchi {telegram_id} roli <b>{role}</b> ga o'zgartirildi.",

        # Информация о пользователе (/me)
        "me_info": (
            "👤 <b>Sizning ma'lumotlaringiz (/me)</b>\n\n"
            "<b>Telegram ID:</b> <code>{telegram_id}</code>\n"
            "<b>Ism:</b> {first_name}\n"
            "<b>Familiya:</b> {last_name}\n"
            "<b>Sinf:</b> {class_name}\n"
            "<b>Rol:</b> {role}"
        ),

        # Список пользователей (/users)
        "users_list_title": "👥 <b>Ro'yxatdan o'tgan foydalanuvchilar:</b>\n",
        "no_users": "Foydalanuvchilar topilmadi.",
        "user_item_format": (
            "<b>ID:</b> {id} | <b>TG ID:</b> <code>{telegram_id}</code>\n"
            "<b>F.I.SH:</b> {first_name} {last_name}\n"
            "<b>Sinf:</b> {class_name} | <b>Rol:</b> {role}\n"
            "───────────────"
        ),

        # Новости
        "news_list_title": "📰 <b>So'nggi yangiliklar:</b>",
        "no_news": "📰 <b>Yangiliklar</b>\n\nHozircha yangi maktab yangiliklari yo'q.",
        "btn_back_to_list": "⬅️ Yangiliklarga qaytish",
        "btn_next_page": "Keyingisi ➡️",
        "btn_prev_page": "⬅️ Ortga",
        "news_format": "📰 <b>{title}</b>\n\n📅 <i>{date}</i>\n\n{content}",

        # Обращения
        "ask_complaint": "📩 <b>Yangi shikoyat</b>\n\nMuammoni bitta xabarda tasvirlab bering.",
        "ask_suggestion": "💡 <b>Yangi taklif</b>\n\nMaktab uchun g'oya yoki taklifingizni yozing.",
        "ask_question": "❓ <b>Savol yoki iltimos</b>\n\nSizga nima bo'yicha yordam kerakligini bitta xabarda yozing.",
        "complaint_warning": (
            "⚠️ <b>Shikoyat yuborishdan oldin</b>\n\n"
            "Murojaat haqiqiy maktab muammolari uchun mo'ljallangan.\n\n"
            "Quyidagilarni yubormang:\n• haqoratlar;\n• tahdidlar;\n• nomaqbul yoki jinsiy mazmundagi kontent;\n• spam;\n• ma'nosiz sinov xabarlari.\n\n"
            "Murojaat texnik jihatdan akkauntingiz bilan bog'langan. Qoidalar jiddiy buzilsa, ma'muriyat muallifni aniqlashi mumkin.\n\n"
            "Tizimdan mas'uliyat bilan foydalaning."
        ),
        "suggestion_warning": (
            "💡 <b>Taklif yuborishdan oldin</b>\n\n"
            "Takliflar maktabni yaxshilash bo'yicha foydali g'oyalar uchun mo'ljallangan.\n\n"
            "Quyidagilarni yubormang:\n• spam;\n• haqoratlar;\n• ma'nosiz xabarlar;\n• nomaqbul kontent.\n\n"
            "Xabar texnik jihatdan muallif akkaunti bilan bog'langan. Suiste'mol qilinsa, ma'muriyat yuboruvchini aniqlashi mumkin."
        ),
        "btn_complaint_continue": "✅ Tushundim",
        "btn_suggestion_continue": "✅ Davom etish",
        "feedback_warning_waiting": "Xabar ostidan «Davom etish» yoki «Bekor qilish»ni tanlang.",
        "feedback_warning_accepted": "✅ Qabul qilindi. Endi murojaatni bitta xabarda yozing.",
        "confirm_feedback": "Xabarni ma'muriyatga yuborasizmi?\n\n<b>Matn:</b>\n{text}",
        "btn_confirm_yes": "✅ Yuborish",
        "btn_confirm_no": "❌ Bekor qilish",
        "btn_cancel": "❌ Bekor qilish",
        "feedback_sent": "✅ Murojaatingiz ma'muriyatga yuborildi.",
        "feedback_cancelled": "Murojaat yuborish bekor qilindi.",
        "feedback_waiting_confirmation": "Xabar ostidan «Yuborish» yoki «Bekor qilish»ni tanlang.",
        "my_feedbacks_title": "📨 <b>Mening murojaatlarim</b>",
        "no_my_feedbacks": "📨 <b>Mening murojaatlarim</b>\n\nSiz hali murojaat yubormagansiz.",
        "my_feedback_item": "{type} #{id} — {status}",
        "my_feedback_detail": "{type} #{id}\n\n📅 Sana: {date}\n📌 Holat: {status}\n\n<b>Matn:</b>\n{text}",
        "btn_back_to_feedbacks": "⬅️ Murojaatlarimga",
        "help_text": (
            "📚 <b>Maktab boti nimalarni qila oladi?</b>\n\n"
            "📰 /news — yangiliklar\n📅 /schedule — dars jadvali\n🎯 /events — tadbirlar\n🏆 /achievements — yutuqlar\n"
            "🎮 /games — xotira va mantiq mashqlari\n👥 /class — mening sinfim\n📨 murojaatlar — maktab bilan aloqa\n"
            "👤 /profile — profil\n❓ /help — yordam"
        ),
        "help_staff": "\n\n👨‍🏫 <b>Xodim uchun</b>\n/staff — sinflar, o'quvchilar, arizalar, e'lonlar, jadval va statistika.",
        "help_admin": "\n\n🛠 <b>Administrator uchun</b>\n/admin — foydalanuvchilar, sinflar, yangiliklar, murojaatlar, xabar tarqatish va sozlamalar.",
        "type_complaint": "📩 Shikoyat",
        "type_suggestion": "💡 Taklif",
        "type_question": "❓ Savol / iltimos",
        "status_new": "Yangi",
        "status_in_progress": "Jarayonda",
        "status_closed": "Yopilgan",
        "admin_feedback_notification": (
            "📩 <b>Yangi murojaat!</b>\n\n"
            "<b>Turi:</b> {type}\n"
            "<b>Ism:</b> {first_name}\n"
            "<b>Familiya:</b> {last_name}\n"
            "<b>Sinf:</b> {class_name}\n"
            "<b>Sana:</b> {date}\n\n"
            "<b>Matn:</b>\n{text}"
        ),
        "admin_feedbacks_title": "📋 <b>So'nggi murojaatlar:</b>\n",
        "no_feedbacks": "Hozircha murojaatlar yo'q.",
        "feedback_item_format": (
            "<b>#{id} [{type}]</b> — Holat: <i>{status}</i>\n"
            "<b>Kimdan:</b> {first_name} {last_name} ({class_name})\n"
            "<b>Sana:</b> {date}\n"
            "<b>Matn:</b> {text}\n"
            "───────────────"
        ),

        # Profil
        "lang_name_ru": "Ruscha",
        "lang_name_uz": "O'zbekcha",
        "profile_card": (
            "👤 <b>Mening profilim</b>\n\n"
            "👨 Ism: {first_name}\n"
            "👨 Familiya: {last_name}\n"
            "🏫 Sinf: {class_name}\n"
            "🌐 Til: {language}\n"
            "🎓 Rol: {role}\n"
            "🆔 Kod: <code>{user_code}</code>\n"
            "📅 Ro'yxatdan o'tgan sana: {created_at}"
        ),
        "btn_edit_profile": "✏️ Profilni tahrirlash",
        "btn_edit_first_name": "Ism",
        "btn_edit_last_name": "Familiya",
        "btn_edit_class": "Sinf",
        "btn_edit_language": "Til",
        "btn_change_class_request": "🔄 Sinfni almashtirish so'rovi",
        "btn_public_profile_enable": "🔗 Reytingda havolani ko'rsatish",
        "btn_public_profile_disable": "🔒 Reytingda havolani yashirish",
        "public_profile_enabled": "Agar username mavjud bo'lsa, Telegram havolasi reytingda ko'rsatiladi.",
        "public_profile_disabled": "Telegram havolasi reytingda yashirildi.",
        "class_change_title": "🔄 <b>Sinfni almashtirish</b>\n\nYangi parallelni tanlang:",
        "class_change_choose_class": "🔄 <b>Sinfni almashtirish</b>\n\nYangi sinfni tanlang:",
        "class_change_reason": "Ko'chirish sababini bitta xabarda yozing yoki bu qadamni o'tkazib yuboring.",
        "class_change_skip_reason": "Sababni o'tkazib yuborish",
        "class_change_confirm": "Hozirgi sinf: <b>{old_class}</b>\nYangi sinf: <b>{new_class}</b>\nSabab: {reason}\n\nSo'rov yuborilsinmi?",
        "class_change_submit": "✅ So'rovni yuborish",
        "class_change_submitted": "✅ Sinfni almashtirish so'rovi yuborildi. Sinfingiz faqat ma'muriyat tasdiqlagandan keyin o'zgaradi.",
        "class_change_pending": "⏳ Sinfni almashtirish bo'yicha ko'rib chiqilayotgan so'rovingiz bor.",
        "class_change_same": "Siz allaqachon shu sinfda o'qiysiz.",
        "class_change_use_request": "Bu ekran yangilandi. Profilni ochib, sinfni almashtirish so'rovini yuboring.",
        "btn_cancel_edit": "⬅️ Orqaga",
        "edit_menu_title": "✏️ <b>Profilni tahrirlash</b>\n\nO'zgartirmoqchi bo'lgan maydonni tanlang.",
        "ask_new_first_name": "Yangi ismni kiriting:",
        "ask_new_last_name": "Yangi familiyani kiriting:",
        "ask_new_class": "Yangi sinfni kiriting:",
        "ask_new_language": "Tilni tanlang:",
        "profile_updated": "✅ Profil yangilandi."
        ,"schedule_title": "📅 <b>Dars jadvali</b>\n🏫 {class_name}\n\nKunni tanlang:",
        "schedule_empty": "Bu kun uchun darslar hali kiritilmagan.",
        "schedule_day": "📅 <b>{day}</b>\n🏫 {class_name}\n\n{lessons}",
        "events_title": "🎯 <b>Yaqin tadbirlar</b>",
        "events_empty": "Yaqin tadbirlar hali yo'q.",
        "achievements_title": "🏆 <b>Maktab yutuqlari</b>",
        "achievements_empty": "E'lon qilingan yutuqlar hali yo'q.",
        "polls_title": "📊 <b>So'rovlar</b>",
        "polls_empty": "Faol so'rovlar hali yo'q.",
        "vote_saved": "✅ Ovoz qabul qilindi.",
        "vote_unavailable": "Bu so'rov yopilgan yoki siz allaqachon ovoz bergansiz.",
        "requests_title": "📨 <b>Murojaatlar</b>\n\nAmalni tanlang:",
        "my_class_title": "👥 <b>Mening sinfim: {class_name}</b>\n\nO'quvchilar: {students}\n\n<b>Bugun:</b>\n{lessons}\n\n<b>So'nggi e'lonlar:</b>\n{announcements}",
        "no_announcements": "Hali yo'q.",
        "btn_back_to_sections": "⬅️ Bo'limlarga",
        "games_home": "🧠 <b>Aql uchun o'yinlar</b>\n\nXotira, diqqat va mantiq uchun qisqa mashqlar.\n\nBu yerda ko'p vaqt o'tkazmang — o'qish va dam olish rekordlardan muhimroq 🙂",
        "game_memory": "🧠 Raqamlarni eslab qolish",
        "game_logic": "🔢 Mantiqiy ketma-ketlik",
        "game_stats": "🏆 Statistika",
        "game_play": "▶️ O'ynash",
        "game_back": "⬅️ Ortga",
        "memory_intro": "🧠 <b>Raqamlarni eslab qolish</b>\n\nRaqamlarni eslab, so'ng ularni aniq tartibda bosing.",
        "memory_level": "🧠 <b>{level}-daraja</b>\n\nRaqamlar va ularning tartibini eslab qoling.",
        "memory_numbers": "🧠 <b>{level}-daraja</b>\n\n<b>{sequence}</b>\n\nEslab qoling…",
        "memory_answer": "🧠 <b>{level}-daraja</b>\n\nRaqamlarni to'g'ri tartibda bosing.",
        "memory_next_number": "🧠 <b>{level}-daraja</b>\n\nTo'g'ri. Keyingi raqamni tanlang.",
        "memory_level_complete": "✅ {level}-daraja o'tildi. Keyingi daraja…",
        "memory_error": "❌ <b>Xato</b>\n\nTo'g'ri ketma-ketlik: <b>{sequence}</b>\nHisob: <b>{score}</b>",
        "memory_complete": "🏁 <b>Raqamlarni eslab qolish yakunlandi!</b>\n\nO'tilgan daraja: <b>{level}</b>\nHisob: <b>{score}</b>",
        "game_retry": "🔁 Qayta o'ynash",
        "logic_intro": "🔢 <b>Mantiqiy ketma-ketlik</b>\n\nQonuniyatlarga oid 5 qisqa savolni yeching.",
        "logic_question": "🔢 <b>Mantiqiy ketma-ketlik</b>\nSavol {round}/5\n\n<b>{sequence}</b>",
        "logic_correct": "✅ To'g'ri!\n\n{explanation}",
        "logic_wrong": "❌ Noto'g'ri. To'g'ri javob: <b>{correct}</b>\n\n{explanation}",
        "logic_next": "➡️ Keyingi savol",
        "logic_complete": "🏁 <b>Mantiqiy ketma-ketlik yakunlandi!</b>\n\nTo'g'ri javoblar: <b>{correct}/5</b>\nHisob: <b>{score}</b>",
        "logic_rule_add": "Har qadamda +{value}.",
        "logic_rule_multiply": "Har qadamda ×{value}.",
        "logic_rule_alternate": "+3, −1, +3, −1…",
        "logic_rule_interleaved": "Ikki almashinuvchi ketma-ketlik.",
        "game_personal_stats": "🏆 <b>O'yinlar statistikasi</b>\n\n🧠 Raqamlarni eslab qolish\nEng yaxshi daraja: <b>{memory_level}</b>\nEng yaxshi hisob: <b>{memory_score}</b>\nO'yinlar: <b>{memory_games}</b>\n\n🔢 Mantiqiy ketma-ketlik\nEng yaxshi hisob: <b>{logic_score}</b>\nEng yaxshi natija: <b>{logic_correct}</b>\nO'yinlar: <b>{logic_games}</b>",
        "game_leaderboard": "🏆 <b>{title}</b>\n\n{rows}",
        "game_leaderboard_empty": "Hali natijalar yo'q."
        ,"leaderboard_week": "hafta uchun"
        ,"leaderboard_all": "barcha vaqt uchun"
        ,"leaderboard_prize_default": "🎁 <b>Haftalik sovrinlar</b>\n\nBa'zan bot yaratuvchisi reyting yetakchilarini Telegram sovg'alari bilan taqdirlaydi. Jadvalni kuzating — sovrin sizga ham nasib qilishi mumkin."
    }
}
