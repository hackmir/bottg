import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import sqlite3
import os
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузите переменные окружения
load_dotenv()

# Получите токен бота и ID администратора
TOKEN = os.getenv("TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not TOKEN or not ADMIN_ID:
    raise ValueError("Не удалось загрузить TOKEN или ADMIN_ID из переменных окружения.")

ADMIN_ID = int(ADMIN_ID)  # Преобразуем ID администратора в число

# Состояния
CHOOSING, BRAND, MODEL, YEAR, PART_NAME = range(5)

# Подключение к базе данных SQLite
def connect_to_db():
    try:
        conn = sqlite3.connect("database.db")  # Файл базы данных
        return conn
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        return None

# Инициализация базы данных (создание таблиц, если их нет)
def init_db():
    conn = connect_to_db()
    if conn:
        try:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS scrapyards (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,        -- Название разборки
                        vehicle_type TEXT NOT NULL, -- Вид авто
                        city TEXT NOT NULL,        -- Город
                        phone TEXT NOT NULL        -- Номер телефона
                    )
                """)
        except Exception as e:
            logger.error(f"Ошибка при создании таблиц: {e}")
        finally:
            conn.close()

# Получение списка разборок
def get_scrapyards():
    conn = connect_to_db()
    if conn:
        try:
            with conn:
                cur = conn.cursor()
                cur.execute("SELECT id, name, vehicle_type, city, phone FROM scrapyards;")
                results = cur.fetchall()
                return results
        except Exception as e:
            logger.error(f"Ошибка при получении списка разборок: {e}")
            return []
    return []

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Найти запчасть"], ["Список разборок"], ["Связаться с нами"]]  # Главное меню
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Наш бот занимается поиском и подбором Б/У запчастей. Выберите, что Вам нужно:", reply_markup=reply_markup)
    return CHOOSING

# Обработка выбора категории
async def handle_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    logger.info(f"Пользователь выбрал: {text}")
    if text == "Б/У запчасти":
        keyboard = [["Назад"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Введите марку автомобиля:", reply_markup=reply_markup)
        return BRAND
    elif text == "Разборки":
        await handle_scrapyards(update, context)
        return ConversationHandler.END
    elif text == "Связаться с нами":
        await handle_contact_admin(update, context)
        return CHOOSING

# Обработка марки автомобиля
async def handle_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    logger.info(f"Пользователь ввел марку: {text}")
    if text == "Назад":
        return await start(update, context)
    
    context.user_data['brand'] = text
    keyboard = [["Назад"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Введите модель автомобиля:", reply_markup=reply_markup)
    return MODEL

# Обработка модели автомобиля
async def handle_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    logger.info(f"Пользователь ввел модель: {text}")
    if text == "Назад":
        return await start(update, context)
    
    context.user_data['model'] = text
    keyboard = [["Назад"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Введите год выпуска автомобиля:", reply_markup=reply_markup)
    return YEAR

# Обработка года выпуска
async def handle_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    logger.info(f"Пользователь ввел год: {text}")
    if text == "Назад":
        return await start(update, context)
    
    try:
        year = int(text)  # Проверяем, что год — это число
        context.user_data['year'] = year
        keyboard = [["Назад"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Введите название запчасти:", reply_markup=reply_markup)
        return PART_NAME
    except ValueError:
        await update.message.reply_text("Год должен быть числом. Попробуйте снова.")
        return YEAR

# Обработка названия запчасти
async def handle_part_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    logger.info(f"Пользователь ввел название запчасти: {text}")
    if text == "Назад":
        return await start(update, context)
    
    part_name = text
    user_data = context.user_data

    # Сохраняем данные
    user_data['part_name'] = part_name
    user_data['username'] = update.message.from_user.username
    user_data['user_id'] = update.message.from_user.id

    # Отправляем заявку администратору
    await send_request_to_admin(context, user_data)

    # Отвечаем пользователю
    await update.message.reply_text("Ваша заявка принята, ожидайте.")

    # Очищаем данные
    user_data.clear()
    return ConversationHandler.END

# Обработка кнопки "Связаться с нами"
async def handle_contact_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    logger.info(f"Пользователь @{user.username} хочет связаться с администратором.")
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Пользователь @{user.username} (ID: {user.id}) хочет связаться с вами."
    )
    await update.message.reply_text("Ваш запрос отправлен администратору. Ожидайте ответа.")

# Отправка заявки администратору
async def send_request_to_admin(context: ContextTypes.DEFAULT_TYPE, user_data: dict):
    request_text = (
        "Новая заявка на запчасть:\n"
        f"Марка: {user_data.get('brand')}\n"
        f"Модель: {user_data.get('model')}\n"
        f"Год: {user_data.get('year')}\n"
        f"Запчасть: {user_data.get('part_name')}\n"
        f"Пользователь: @{user_data.get('username')} (ID: {user_data.get('user_id')})"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=request_text)

# Обработка разборок
async def handle_scrapyards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    scrapyards = get_scrapyards()
    if scrapyards:
        response = "Список разборок:\n"
        for scrapyard in scrapyards:
            response += (
                f"ID: {scrapyard[0]}\n"
                f"Название: {scrapyard[1]}\n"
                f"Вид авто: {scrapyard[2]}\n"
                f"Город: {scrapyard[3]}\n"
                f"Телефон: {scrapyard[4]}\n\n"
            )
    else:
        response = "Разборки не найдены."
    await update.message.reply_text(response)

# Функция для отмены диалога
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Диалог завершён.")
    return await start(update, context)  # Возврат в главное меню

# Команда для добавления разборки
async def add_scrapyard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return

    try:
        args = context.args
        if len(args) != 4:
            await update.message.reply_text("Используйте команду так: /add_scrapyard \"Название\" \"Вид авто\" \"Город\" \"Телефон\"")
            return

        name, vehicle_type, city, phone = args
        conn = connect_to_db()
        if conn:
            try:
                with conn:
                    conn.execute("""
                        INSERT INTO scrapyards (name, vehicle_type, city, phone)
                        VALUES (?, ?, ?, ?)
                    """, (name, vehicle_type, city, phone))
                await update.message.reply_text(f"Разборка '{name}' добавлена.")
            finally:
                conn.close()
    except Exception as e:
        logger.error(f"Ошибка при добавлении разборки: {e}")
        await update.message.reply_text("Произошла ошибка при добавлении разборки.")

# Команда для редактирования разборки
async def edit_scrapyard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return

    try:
        args = context.args
        if len(args) != 5:
            await update.message.reply_text("Используйте команду так: /edit_scrapyard ID \"Новое название\" \"Новый вид авто\" \"Новый город\" \"Новый телефон\"")
            return

        scrapyard_id, name, vehicle_type, city, phone = args
        conn = connect_to_db()
        if conn:
            try:
                with conn:
                    conn.execute("""
                        UPDATE scrapyards
                        SET name = ?, vehicle_type = ?, city = ?, phone = ?
                        WHERE id = ?
                    """, (name, vehicle_type, city, phone, scrapyard_id))
                await update.message.reply_text(f"Разборка с ID {scrapyard_id} обновлена.")
            finally:
                conn.close()
    except Exception as e:
        logger.error(f"Ошибка при редактировании разборки: {e}")
        await update.message.reply_text("Произошла ошибка при редактировании разборки.")

# Основная функция
def main():
    init_db()

    application = Application.builder().token(TOKEN).build()

    # Обработчик диалога для "Б/У запчасти"
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category)],
            BRAND: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_brand)],
            MODEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_model)],
            YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_year)],
            PART_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_part_name)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # Регистрируем обработчики
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("add_scrapyard", add_scrapyard_command))
    application.add_handler(CommandHandler("edit_scrapyard", edit_scrapyard_command))

    # Запускаем бота
    application.run_polling()

if __name__ == "__main__":
    main()
