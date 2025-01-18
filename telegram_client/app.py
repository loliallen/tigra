import logging
import json
import os

from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Файл для хранения данных
DATA_FILE = "user_data.json"

# Загрузка данных из файла
def load_data():
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Сохранение данных в файл
def save_data():
    with open(DATA_FILE, "w") as file:
        json.dump(users_data, file, indent=4)

# Хранилище данных
users_data = load_data()


# Функция для формирования главного меню
def get_main_menu():
    return ReplyKeyboardMarkup(
        [["Создать посещение", "Список посещений"],
         ["Добавить ребенка", "Список детей", "Изменить ребенка", "Удалить ребенка"]],
        resize_keyboard=True
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка входящих сообщений."""
    user_id = str(update.effective_user.id)

    if user_id not in users_data:
        # Если пользователь не авторизован, направляем в начало
        return await start(update, context)
    else:
        # Если пользователь уже авторизован, отправляем в главное меню
        return await main_menu(update, context)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало работы и запрос номера телефона."""
    user_id = str(update.effective_user.id)
    user = update.effective_user

    if user_id in users_data:
        # Если пользователь уже есть в данных, перенаправляем в меню
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
        user_id = str(update.effective_user.id)
        users_data[user_id] = {
            "phone": contact.phone_number,
            "children": [],
            "visits": []
        }
        save_data()  # Сохраняем данные
        await update.message.reply_text(
            "Вы успешно авторизовались!",
            reply_markup=get_main_menu()
        )
    else:
        await update.message.reply_text("Пожалуйста, отправьте ваш номер телефона.")

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню."""
    text = update.message.text
    user_id = str(update.effective_user.id)

    if context.user_data.get("adding_child"):
        return await add_child(update, context)
    if context.user_data.get("edit_child_index") is not None:
        if context.user_data.get("edit_field") == "name":
            return await receive_new_name(update, context)
        if context.user_data.get("edit_field") == "birthdate":
            return await receive_new_birthdate(update, context)

    if text == "Создать посещение":
        await update.message.reply_text(
            "Выберите слот времени:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("1 час", callback_data="slot_1"),
                 InlineKeyboardButton("2 часа", callback_data="slot_2"),
                 InlineKeyboardButton("3 часа", callback_data="slot_3")]
            ])
        )
    elif text == "Список посещений":
        visits = users_data.get(user_id, {}).get("visits", [])
        if visits:
            visits_text = "\n".join([f"{i + 1}. Слот: {v['slot']} часов, Участники: {v['participants']}" for i, v in enumerate(visits)])
        else:
            visits_text = "У вас пока нет посещений."
        await update.message.reply_text(visits_text, reply_markup=get_main_menu())
    elif text == "Добавить ребенка":
        await update.message.reply_text("Введите имя ребенка:")
        context.user_data["adding_child"] = True
    elif text == "Список детей":
        children = users_data.get(user_id, {}).get("children", [])
        if children:
            children_text = "\n".join([f"{i + 1}. {child['name']} (Дата рождения: {child['birth_date']})" for i, child in enumerate(children)])
        else:
            children_text = "У вас пока нет добавленных детей."
        await update.message.reply_text(children_text)
    elif text == "Изменить ребенка":
        children = users_data.get(user_id, {}).get("children", [])
        if not children:
            await update.message.reply_text("У вас нет детей для изменения.")
        else:
            # Отправим пользователю список детей для выбора
            child_buttons = [
                [InlineKeyboardButton(f"{child['name']} (Дата рождения: {child['birth_date']})", callback_data=f"edit_{i}")]
                for i, child in enumerate(children)
            ]
            await update.message.reply_text(
                "Выберите ребенка для изменения:",
                reply_markup=InlineKeyboardMarkup(child_buttons)
            )
    elif text == "Удалить ребенка":
        children = users_data.get(user_id, {}).get("children", [])
        if not children:
            await update.message.reply_text("У вас нет детей для удаления.")
        else:
            # Отправим пользователю список детей для выбора
            child_buttons = [
                [InlineKeyboardButton(f"{child['name']} (Дата рождения: {child['birth_date']})", callback_data=f"delete_{i}")]
                for i, child in enumerate(children)
            ]
            await update.message.reply_text(
                "Выберите ребенка для удаления:",
                reply_markup=InlineKeyboardMarkup(child_buttons)
            )
    else:
        await update.message.reply_text("Пожалуйста, выберите действие из меню.", reply_markup=get_main_menu())

async def add_child(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавление ребенка с сохранением имени и даты рождения."""
    user_id = str(update.effective_user.id)

    # Проверяем, на каком этапе находится пользователь
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
                import datetime
                datetime.datetime.strptime(birth_date, "%d.%m.%Y")
            except ValueError:
                # Неверный формат даты
                await update.message.reply_text("Неверный формат даты. Попробуйте еще раз (ДД.ММ.ГГГГ):")
                return

            # Добавляем ребенка в список
            child_name = context.user_data["child_name"]
            users_data[user_id]["children"].append({
                "name": child_name,
                "birth_date": birth_date
            })
            save_data()  # Сохраняем данные в файл

            # Оповещаем пользователя и возвращаем в главное меню
            await update.message.reply_text(
                f"Ребенок {child_name} (Дата рождения: {birth_date}) успешно добавлен!",
                reply_markup=get_main_menu()
            )

            # Очищаем данные
            del context.user_data["adding_child"]
            del context.user_data["child_name"]

    else:
        # Инициализируем процесс добавления ребенка
        context.user_data["adding_child"] = True
        await update.message.reply_text("Введите имя ребенка:")

# Обработчик изменения ребенка
async def edit_child(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Изменение информации о ребенке."""
    query = update.callback_query
    child_index = int(query.data.split("_")[-1])
    user_id = str(update.effective_user.id)
    child = users_data[user_id]["children"][child_index]

    # Запрос на изменение имени или даты рождения
    await query.answer()
    await query.edit_message_text(
        text=f"Вы выбрали ребенка: {child['name']} (Дата рождения: {child['birth_date']}).\n\nЧто вы хотите изменить?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Изменить имя", callback_data=f"edit_name_{child_index}")],
            [InlineKeyboardButton("Изменить дату рождения", callback_data=f"edit_birthdate_{child_index}")]
        ])
    )

# Обработчик изменения имени
async def change_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Изменение имени ребенка."""
    query = update.callback_query
    child_index = int(query.data.split("_")[2])
    user_id = str(update.effective_user.id)
    child = users_data[user_id]["children"][child_index]

    await query.answer()
    await query.edit_message_text(
        text=f"Вы выбрали ребенка: {child['name']}. Введите новое имя:"
    )
    context.user_data["edit_child_index"] = child_index
    context.user_data["edit_field"] = "name"


# Обработчик получения нового имени
async def receive_new_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нового имени для ребенка."""
    user_id = str(update.effective_user.id)
    child_index = context.user_data["edit_child_index"]
    new_name = update.message.text

    # Обновляем имя ребенка в данных
    users_data[user_id]["children"][child_index]["name"] = new_name
    save_data()

    await update.message.reply_text(
        f"Имя ребенка успешно изменено на: {new_name}",
        reply_markup=get_main_menu()
    )

    # Очищаем данные из контекста
    del context.user_data["edit_child_index"]
    del context.user_data["edit_field"]


# Обработчик изменения даты рождения
async def change_birthdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Изменение даты рождения ребенка."""
    query = update.callback_query
    child_index = int(query.data.split("_")[2])
    user_id = str(update.effective_user.id)
    child = users_data[user_id]["children"][child_index]

    await query.answer()
    await query.edit_message_text(
        text=f"Вы выбрали ребенка: {child['name']}. Введите новую дату рождения в формате ДД.ММ.ГГГГ:"
    )
    context.user_data["edit_child_index"] = child_index
    context.user_data["edit_field"] = "birthdate"


# Обработчик получения новой даты рождения
async def receive_new_birthdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка новой даты рождения для ребенка."""
    user_id = str(update.effective_user.id)
    child_index = context.user_data["edit_child_index"]
    new_birthdate = update.message.text

    try:
        # Проверка формата даты
        import datetime
        datetime.datetime.strptime(new_birthdate, "%d.%m.%Y")
    except ValueError:
        # Неверный формат даты
        await update.message.reply_text("Неверный формат даты. Попробуйте еще раз (ДД.ММ.ГГГГ):")
        return

    # Обновляем дату рождения ребенка в данных
    users_data[user_id]["children"][child_index]["birth_date"] = new_birthdate
    save_data()

    await update.message.reply_text(
        f"Дата рождения ребенка успешно изменена на: {new_birthdate}",
        reply_markup=get_main_menu()
    )

    # Очищаем данные из контекста
    del context.user_data["edit_child_index"]
    del context.user_data["edit_field"]


# Обработчик удаления ребенка
async def delete_child(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаление ребенка из списка."""
    query = update.callback_query
    child_index = int(query.data.split("_")[1])
    user_id = str(update.effective_user.id)

    # Удаляем ребенка из списка
    users_data[user_id]["children"].pop(child_index)
    save_data()

    await query.answer()
    await query.edit_message_text(
        text="Ребенок успешно удален из списка!",
        # reply_markup=get_main_menu()
    )


async def select_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор слота времени."""
    query = update.callback_query
    await query.answer()
    slot = int(query.data.split("_")[1])
    context.user_data["slot"] = slot
    await query.edit_message_text(
        text="Выберите количество участников:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{i} участник(ов)", callback_data=f"participants_{i}") for i in range(1, 6)]
        ])
    )

async def select_participants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор количества участников."""
    query = update.callback_query
    await query.answer()
    participants = int(query.data.split("_")[1])
    user_id = str(update.effective_user.id)
    users_data[user_id]["visits"].append({
        "slot": context.user_data["slot"],
        "participants": participants
    })
    save_data()  # Сохраняем данные
    await query.edit_message_text(
        text=f"Посещение на {context.user_data['slot']} часов для {participants} участников создано."
    )


BOT_TOKEN = os.getenv("BOT_TOKEN")

def main():
    """Основная функция для запуска бота."""
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.CONTACT, authorize))

    application.add_handler(CallbackQueryHandler(select_slot, pattern="^slot_"))
    application.add_handler(CallbackQueryHandler(select_participants, pattern="^participants_"))
    application.add_handler(CallbackQueryHandler(change_name, pattern="^edit_name_"))
    application.add_handler(CallbackQueryHandler(change_birthdate, pattern="^edit_birthdate_"))
    application.add_handler(CallbackQueryHandler(edit_child, pattern="^edit_"))
    application.add_handler(CallbackQueryHandler(delete_child, pattern="^delete_"))

    application.run_polling(timeout=3)

if __name__ == "__main__":
    main()
