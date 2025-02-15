from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Подключение к базе данных
def get_db_connection():
    conn = sqlite3.connect('autoparts.db')
    conn.row_factory = sqlite3.Row
    return conn

# Главная страница (список разборок)
@app.route('/')
def index():
    conn = get_db_connection()
    scrapyards = conn.execute('SELECT * FROM scrapyards').fetchall()
    conn.close()
    return render_template('index.html', scrapyards=scrapyards)

# Добавление разборки
@app.route('/add', methods=['GET', 'POST'])
def add_scrapyard():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']

        conn = get_db_connection()
        conn.execute('INSERT INTO scrapyards (name, phone) VALUES (?, ?)',
                     (name, phone))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    return render_template('add.html')

# Редактирование разборки
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_scrapyard(id):
    conn = get_db_connection()
    scrapyard = conn.execute('SELECT * FROM scrapyards WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']

        conn.execute('UPDATE scrapyards SET name = ?, phone = ? WHERE id = ?',
                     (name, phone, id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    conn.close()
    return render_template('edit.html', scrapyard=scrapyard)

# Удаление разборки
@app.route('/delete/<int:id>')
def delete_scrapyard(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM scrapyards WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
