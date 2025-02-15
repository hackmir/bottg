from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import psycopg2
import os
from dotenv import load_dotenv

# Загрузите переменные окружения
load_dotenv()

# Получите токен бота
TOKEN = os.getenv("TOKEN")

# Состояния
BRAND, MODEL, YEAR, PART_NAME = range(4)

# Подключение к базе данных
def connect_to_db():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host="amvera-hackmir-cnpg-raz-rw",  # Доменное имя для чтения/записи
            port=int(os.getenv("DB_PORT"))  # Порт (обычно 5432)
        )
        return conn
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None

# Получение списка разборок
def get_scrapyards():
    conn = connect_to_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM scrapyards;")
                results = cur.fetchall()
                return results
        finally:
            conn.close()
    return []

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Найти запчасть"], ["Список разборок"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Наш бот занимаеться поиском и подбором Б/У запчастей. Выберете что Вам нужно:", reply_markup=reply_markup)

# Обработка выбора категории
async def handle_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Б/У запчасти":
        await update.message.reply_text("Введите марку автомобиля:")
        return BRAND
    elif text == "Разборки":
        await handle_scrapyards(update, context)
        return ConversationHandler.END

# Обработка марки автомобиля
async def handle_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    brand = update.message.text
    context.user_data['brand'] = brand
    await update.message.reply_text("Введите модель автомобиля:")
    return MODEL

# Обработка модели автомобиля
async def handle_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    model = update.message.text
    context.user_data['model'] = model
    await update.message.reply_text("Введите год выпуска автомобиля:")
    return YEAR

# Обработка года выпуска
async def handle_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    year = update.message.text
    context.user_data['year'] = year
    await update.message.reply_text("Введите название запчасти:")
    return PART_NAME

# Обработка названия запчасти
async def handle_part_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    part_name = update.message.text
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

# Обработка разборок
async def handle_scrapyards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    scrapyards = get_scrapyards()
    if scrapyards:
        response = "Список разборок:\n"
        for scrapyard in scrapyards:
            response += f"{scrapyard[1]}: {scrapyard[2]}\n"
    else:
        response = "Разборки не найдены."
    await update.message.reply_text(response)

# Функция для отмены диалога
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Очищаем данные пользователя
    context.user_data.clear()
    # Отправляем сообщение о завершении
    await update.message.reply_text("Диалог завершён.")
    return ConversationHandler.END

# Основная функция
def main():
    application = Application.builder().token(TOKEN).build()

    # Обработчик диалога для "Б/У запчасти"
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category)],
        states={
            BRAND: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_brand)],
            MODEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_model)],
            YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_year)],
            PART_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_part_name)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == "__main__":
    main()
