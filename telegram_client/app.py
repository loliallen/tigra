import logging
import os
from pathlib import Path

from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters, PicklePersistence, PersistenceInput
)
from django_client import DjangoClient

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Создаем директорию для хранения данных если её нет
PERSISTENCE_DIR = Path(__file__).parent / "data"
PERSISTENCE_DIR.mkdir(exist_ok=True)

# Инициализация Django клиента
django_client = DjangoClient()

# Функция для формирования главного меню
def get_main_menu():
    return ReplyKeyboardMarkup(
        [["Создать посещение", "Список посещений"],
         ["Добавить ребенка", "Список детей",],
         ["Изменить ребенка", "Удалить ребенка"]],
        resize_keyboard=True
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка входящих сообщений."""
    user_id = str(update.effective_user.id)

    if "django_user" not in context.user_data:
        # Если пользователь не авторизован, направляем в начало
        return await start(update, context)
    else:
        # Если пользователь уже авторизован, отправляем в главное меню
        return await main_menu(update, context)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало работы и запрос номера телефона."""
    user = update.effective_user

    if "django_user" in context.user_data:
        # Если пользователь уже авторизован, перенаправляем в меню
        await update.message.reply_text(
            f"Добро пожаловать обратно, {user.first_name}!",
            reply_markup=get_main_menu()
        )
    else:
        # Новый пользователь
        await update.message.reply_text(
            f"Здравствуйте, {user.first_name}!\nДля работы с ботом авторизуйтесь, отправив свой номер телефона.",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("Отправить номер телефона", request_contact=True)]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )

async def authorize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Авторизация пользователя."""
    contact = update.message.contact
    if contact:
        # Получаем или создаем пользователя в Django
        django_user = await django_client.get_or_create_user(contact.phone_number)
        context.user_data["django_user"] = django_user
        
        # Проверяем, есть ли у пользователя привязанный магазин
        if not (await django_user.user).store:
            # Получаем список магазинов
            stores = await django_client.get_stores()
            if not stores:
                await update.message.reply_text("Нет доступных магазинов.")
                return
            
            # Создаем кнопки для выбора магазина
            store_buttons = [
                [InlineKeyboardButton(
                    store.address,
                    callback_data=f"register_store_{store.id}"
                )]
                for store in stores
            ]
            
            await update.message.reply_text(
                "Выберите точку:",
                reply_markup=InlineKeyboardMarkup(store_buttons)
            )
        else:
            await update.message.reply_text(
                "Вы успешно авторизовались!",
                reply_markup=get_main_menu()
            )
    else:
        await update.message.reply_text("Пожалуйста, отправьте ваш номер телефона.")

async def select_register_store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора магазина при регистрации."""
    query = update.callback_query
    store_id = int(query.data.split('_')[2])
    
    # Обновляем магазин пользователя
    django_user = context.user_data.get("django_user")
    django_user = await django_client.update_user_store(django_user, store_id)
    context.user_data["django_user"] = django_user
    
    await query.message.reply_text(
        "Вы успешно авторизовались!",
        reply_markup=get_main_menu()
    )

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню."""
    text = update.message.text
    django_user = context.user_data.get("django_user")

    if context.user_data.get("adding_child"):
        return await add_child(update, context)
    if context.user_data.get("edit_child_index") is not None:
        if context.user_data.get("edit_field") == "name":
            return await receive_new_name(update, context)
        if context.user_data.get("edit_field") == "birthdate":
            return await receive_new_birthdate(update, context)

    if text == "Создать посещение":
        buttons = [
            [
                InlineKeyboardButton("1 час", callback_data="slot_1"),
                InlineKeyboardButton("Сертификат", callback_data="slot_2"),
                InlineKeyboardButton("3 часа", callback_data="slot_3")
            ]
        ]
        is_free_visit = await django_client.user_has_free_visit(django_user)
        if is_free_visit:
            buttons.append(
                [InlineKeyboardButton("Использовать бонусное посещение", callback_data="slot_1")]
            )
        cnt_to_free_visit = await django_client.user_count_to_free_visit(django_user)
        if is_free_visit:
            text = "Выберите слот времени:"
        else:
            text = f"Выберите слот времени (до бонусного визита {cnt_to_free_visit} посещения):"
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    elif text == "Список посещений":
        visits = await django_client.get_user_visits(django_user)
        if visits:
            visits_text = []
            for i, visit in enumerate(visits):
                children_names = await django_client.get_visit_children_names(visit)
                visits_text.append(
                    f"{i + 1}. Дата: {visit.date.strftime('%d.%m.%Y %H:%M')}, "
                    f"Продолжительность: {visit.duration // 3600} ч., "
                    f"Дети: {', '.join(children_names)}"
                )
            visits_text = "\n".join(visits_text)
        else:
            visits_text = "У вас пока нет посещений."
        await update.message.reply_text(visits_text, reply_markup=get_main_menu())
    elif text == "Добавить ребенка":
        await update.message.reply_text("Введите имя ребенка:")
        context.user_data["adding_child"] = True
    elif text == "Список детей":
        children = await django_client.get_user_children(django_user)
        if children:
            children_text = "\n".join([
                f"{i + 1}. {child.name} "
                f"(Дата рождения: {child.birth_date.strftime('%d.%m.%Y')})"
                for i, child in enumerate(children)
            ])
        else:
            children_text = "У вас пока нет добавленных детей."
        await update.message.reply_text(children_text)
    elif text == "Изменить ребенка":
        children = await django_client.get_user_children(django_user)
        if not children:
            await update.message.reply_text("У вас нет детей для изменения.")
        else:
            child_buttons = [
                [InlineKeyboardButton(
                    f"{child.name} (Дата рождения: {child.birth_date.strftime('%d.%m.%Y')})",
                    callback_data=f"edit_{child.id}"
                )]
                for child in children
            ]
            await update.message.reply_text(
                "Выберите ребенка для изменения:",
                reply_markup=InlineKeyboardMarkup(child_buttons)
            )
    elif text == "Удалить ребенка":
        children = await django_client.get_user_children(django_user)
        if not children:
            await update.message.reply_text("У вас нет детей для удаления.")
        else:
            child_buttons = [
                [InlineKeyboardButton(
                    f"{child.name} (Дата рождения: {child.birth_date.strftime('%d.%m.%Y')})",
                    callback_data=f"delete_{child.id}"
                )]
                for child in children
            ]
            await update.message.reply_text(
                "Выберите ребенка для удаления:",
                reply_markup=InlineKeyboardMarkup(child_buttons)
            )
    else:
        await update.message.reply_text("Пожалуйста, выберите действие из меню.", reply_markup=get_main_menu())

async def add_child(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавление ребенка."""
    django_user = context.user_data.get("django_user")

    if "adding_child" in context.user_data and context.user_data["adding_child"]:
        if "child_name" not in context.user_data:
            # Сохраняем имя ребенка
            context.user_data["child_name"] = update.message.text
            await update.message.reply_text("Введите дату рождения ребенка в формате ДД.ММ.ГГГГ:")
        else:
            # Сохраняем дату рождения ребенка
            birth_date = update.message.text
            try:
                # Проверка формата даты
                child = await django_client.add_child(
                    django_user,
                    context.user_data["child_name"],
                    birth_date
                )
                
                # Очищаем данные
                del context.user_data["adding_child"]
                del context.user_data["child_name"]
                
                await update.message.reply_text(
                    f"Ребенок {child.name} успешно добавлен!",
                    reply_markup=get_main_menu()
                )
            except ValueError:
                await update.message.reply_text("Неверный формат даты. Попробуйте еще раз (ДД.ММ.ГГГГ):")

async def edit_child(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора ребенка для редактирования."""
    query = update.callback_query
    child_id = int(query.data.split('_')[1])
    context.user_data["edit_child_id"] = child_id
    
    await query.message.reply_text(
        "Что вы хотите изменить?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Имя", callback_data="change_name"),
             InlineKeyboardButton("Дату рождения", callback_data="change_birthdate")]
        ])
    )

async def change_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запрос нового имени."""
    query = update.callback_query
    context.user_data["edit_field"] = "name"
    await query.message.reply_text("Введите новое имя:")

async def receive_new_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нового имени."""
    new_name = update.message.text
    child_id = context.user_data["edit_child_id"]
    
    child = await django_client.update_child(child_id, name=new_name)
    
    del context.user_data["edit_child_id"]
    del context.user_data["edit_field"]
    
    await update.message.reply_text(
        f"Имя успешно изменено на {child.name}!",
        reply_markup=get_main_menu()
    )

async def change_birthdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запрос новой даты рождения."""
    query = update.callback_query
    context.user_data["edit_field"] = "birthdate"
    await query.message.reply_text("Введите новую дату рождения в формате ДД.ММ.ГГГГ:")

async def receive_new_birthdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка новой даты рождения."""
    new_birthdate = update.message.text
    child_id = context.user_data["edit_child_id"]
    
    try:
        child = await django_client.update_child(child_id, birth_date_str=new_birthdate)
        del context.user_data["edit_child_id"]
        del context.user_data["edit_field"]
        
        await update.message.reply_text(
            f"Дата рождения успешно изменена на {child.birth_date.strftime('%d.%m.%Y')}!",
            reply_markup=get_main_menu()
        )
    except ValueError:
        await update.message.reply_text("Неверный формат даты. Попробуйте еще раз (ДД.ММ.ГГГГ):")

async def delete_child(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаление ребенка."""
    query = update.callback_query
    child_id = int(query.data.split('_')[1])
    
    await django_client.delete_child(child_id)
    
    await query.message.reply_text(
        "Ребенок успешно удален!",
        reply_markup=get_main_menu()
    )

async def select_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора временного слота."""
    query = update.callback_query
    slot = int(query.data.split('_')[1])
    context.user_data["selected_slot"] = slot
    
    # Получаем список детей пользователя
    django_user = context.user_data.get("django_user")
    children = await django_client.get_user_children(django_user)
    
    if not children:
        await query.message.reply_text(
            "У вас нет добавленных детей. Сначала добавьте детей.",
            reply_markup=get_main_menu()
        )
        return
    
    # Создаем кнопки для выбора детей
    child_buttons = [
        [InlineKeyboardButton(
            f"{child.name}",
            callback_data=f"child_{child.id}"
        )]
        for child in children
    ]
    child_buttons.append([InlineKeyboardButton("Готово", callback_data="finish_selection")])
    
    context.user_data["selected_children"] = []
    
    await query.message.reply_text(
        "Выберите детей для посещения (можно выбрать несколько):",
        reply_markup=InlineKeyboardMarkup(child_buttons)
    )

async def select_participants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора участников."""
    query = update.callback_query
    
    if query.data == "finish_selection":
        if not context.user_data.get("selected_children"):
            await query.message.reply_text("Выберите хотя бы одного ребенка.")
            return
        
        # Создаем посещение
        django_user = context.user_data.get("django_user")
        slot = context.user_data["selected_slot"]
        children_ids = context.user_data["selected_children"]
        
        visit = await django_client.create_visit(django_user, slot, children_ids, (await django_user.user).store.id)
        children_names = await django_client.get_visit_children_names(visit)
        
        # Очищаем временные данные
        del context.user_data["selected_slot"]
        del context.user_data["selected_children"]
        
        await query.message.reply_text(
            f"Посещение успешно создано!\n"
            f"Дата: {visit.date.strftime('%d.%m.%Y %H:%M')}\n"
            f"Продолжительность: {visit.duration // 3600} ч.\n"
            f"Магазин: {visit.store.address}\n"
            f"Участники: {', '.join(children_names)}",
            reply_markup=get_main_menu()
        )
    else:
        child_id = int(query.data.split('_')[1])
        selected_children = context.user_data.get("selected_children", [])
        
        if child_id in selected_children:
            selected_children.remove(child_id)
            await query.answer("Ребенок удален из списка")
        else:
            selected_children.append(child_id)
            await query.answer("Ребенок добавлен в список")
        
        context.user_data["selected_children"] = selected_children

def main():
    """Запуск бота."""
    # Получаем токен из переменной окружения
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("Пожалуйста, установите переменную окружения BOT_TOKEN")

    # Создаем хранилище для данных
    persistence = PicklePersistence(
        filepath=str(PERSISTENCE_DIR / "bot_data.pickle"),
        store_data=PersistenceInput(
            bot_data=True,
            chat_data=True,
            user_data=True,
            callback_data=False
        )
    )

    # Создаем приложение с поддержкой сохранения данных
    application = ApplicationBuilder().token(token).persistence(persistence).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.CONTACT, authorize))
    application.add_handler(CallbackQueryHandler(select_slot, pattern="^slot_"))
    application.add_handler(CallbackQueryHandler(select_participants, pattern="^(child_|finish_)"))
    application.add_handler(CallbackQueryHandler(select_register_store, pattern="^register_store_"))
    application.add_handler(CallbackQueryHandler(edit_child, pattern="^edit_"))
    application.add_handler(CallbackQueryHandler(delete_child, pattern="^delete_"))
    application.add_handler(CallbackQueryHandler(change_name, pattern="^change_name$"))
    application.add_handler(CallbackQueryHandler(change_birthdate, pattern="^change_birthdate$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
