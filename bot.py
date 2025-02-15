from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import psycopg2
import os
from config import TOKEN, ADMIN_ID

# Получение данных из переменных окружения
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# Функция для подключения к базе данных
def connect_to_db():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None

# Функция для поиска запчастей
def search_parts(part_name: str):
    conn = connect_to_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM parts WHERE name ILIKE %s;", (f"%{part_name}%",))
                results = cur.fetchall()
                return results
        finally:
            conn.close()
    return []

# Функция для получения списка разборок
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
    keyboard = [["Б/У запчасти"], ["Разборки"]]  # Убрали "Новые запчасти"
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите категорию:", reply_markup=reply_markup)

# Обработка выбора категории
async def handle_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Б/У запчасти":
        await update.message.reply_text("Введите название запчасти:")
        context.user_data['category'] = 'used'  # Сохраняем выбранную категорию
    elif text == "Разборки":
        await handle_scrapyards(update, context)

# Обработка ввода названия запчасти
async def handle_part_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    part_name = update.message.text
    results = search_parts(part_name)  # Ищем запчасти

    if results:
        response = "Результаты поиска:\n"
        for part in results:
            response += f"{part[1]} ({part[2]}): {part[3]} руб.\n"
    else:
        response = "Запчасти не найдены."

    await update.message.reply_text(response)

# Обработка выбора "Разборки"
async def handle_scrapyards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    scrapyards = get_scrapyards()  # Получаем список разборок

    if scrapyards:
        response = "Список разборок:\n"
        for scrapyard in scrapyards:
            response += f"{scrapyard[1]}: {scrapyard[2]}\n"
    else:
        response = "Разборки не найдены."

    await update.message.reply_text(response)

# Обработчик для добавления разборки (только для администратора)
async def add_scrapyard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return

    try:
        name, phone = context.args  # Ожидаем два аргумента: название и номер
        conn = connect_to_db()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO scrapyards (name, phone) VALUES (%s, %s);", (name, phone))
                    conn.commit()
                await update.message.reply_text(f"Разборка '{name}' добавлена.")
            finally:
                conn.close()
    except ValueError:
        await update.message.reply_text("Используйте команду так: /add_scrapyard Название Номер")

# Обработчик для редактирования разборки (только для администратора)
async def edit_scrapyard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return

    try:
        scrapyard_id, new_name, new_phone = context.args
        conn = connect_to_db()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("UPDATE scrapyards SET name = %s, phone = %s WHERE id = %s;", (new_name, new_phone, scrapyard_id))
                    conn.commit()
                await update.message.reply_text(f"Разборка с ID {scrapyard_id} обновлена.")
            finally:
                conn.close()
    except ValueError:
        await update.message.reply_text("Используйте команду так: /edit_scrapyard ID Новое_название Новый_номер")

# Обработчик для удаления разборки (только для администратора)
async def delete_scrapyard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return

    try:
        scrapyard_id = context.args[0]
        conn = connect_to_db()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM scrapyards WHERE id = %s;", (scrapyard_id,))
                    conn.commit()
                await update.message.reply_text(f"Разборка с ID {scrapyard_id} удалена.")
            finally:
                conn.close()
    except ValueError:
        await update.message.reply_text("Используйте команду так: /delete_scrapyard ID")

# Основная функция
def main():
    application = Application.builder().token(TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_part_name))
    application.add_handler(CommandHandler("add_scrapyard", add_scrapyard_command))
    application.add_handler(CommandHandler("edit_scrapyard", edit_scrapyard_command))
    application.add_handler(CommandHandler("delete_scrapyard", delete_scrapyard_command))

    # Запускаем бота
    application.run_polling()

if __name__ == "__main__":
    main()
