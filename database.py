import sqlite3

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('autoparts.db')
    cursor = conn.cursor()

    # Таблица для запчастей
    cursor.execute('''CREATE TABLE IF NOT EXISTS parts
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       name TEXT NOT NULL,
                       condition TEXT NOT NULL,
                       price REAL NOT NULL)''')

    # Таблица для разборок
    cursor.execute('''CREATE TABLE IF NOT EXISTS scrapyards
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       name TEXT NOT NULL,
                       phone TEXT NOT NULL)''')

    conn.commit()
    conn.close()

# Добавление запчасти
def add_part(name, condition, price):
    conn = sqlite3.connect('autoparts.db')
    cursor = conn.cursor()

    cursor.execute('INSERT INTO parts (name, condition, price) VALUES (?, ?, ?)',
                   (name, condition, price))

    conn.commit()
    conn.close()

# Поиск запчастей
def search_parts(name):
    conn = sqlite3.connect('autoparts.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM parts WHERE name LIKE ?', (f"%{name}%",))
    results = cursor.fetchall()

    conn.close()
    return results

# Добавление разборки
def add_scrapyard(name, phone):
    conn = sqlite3.connect('autoparts.db')
    cursor = conn.cursor()

    cursor.execute('INSERT INTO scrapyards (name, phone) VALUES (?, ?)',
                   (name, phone))

    conn.commit()
    conn.close()

# Получение списка разборок
def get_scrapyards():
    conn = sqlite3.connect('autoparts.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM scrapyards')
    results = cursor.fetchall()

    conn.close()
    return results

# Редактирование разборки
def edit_scrapyard(scrapyard_id, new_name, new_phone):
    conn = sqlite3.connect('autoparts.db')
    cursor = conn.cursor()

    cursor.execute('UPDATE scrapyards SET name = ?, phone = ? WHERE id = ?',
                   (new_name, new_phone, scrapyard_id))

    conn.commit()
    conn.close()

# Удаление разборки
def delete_scrapyard(scrapyard_id):
    conn = sqlite3.connect('autoparts.db')
    cursor = conn.cursor()

    cursor.execute('DELETE FROM scrapyards WHERE id = ?', (scrapyard_id,))

    conn.commit()
    conn.close()
