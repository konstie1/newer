from pyrogram import Client, filters
import configparser
import sqlite3
import threading

# Конфигурация и создание клиента Pyrogram
config = configparser.ConfigParser()
config.read('config.ini')

api_id = config['DATA']['api_id']
api_hash = config['DATA']['api_hash']
news_id = config['DATA']['news']

app = Client("my_account", api_id=api_id, api_hash=api_hash)

# Использование Thread-local storage для соединения с базой данных
thread_local = threading.local()

def get_db_connection() -> sqlite3.Connection:
    if not hasattr(thread_local, "conn"):
        thread_local.conn = sqlite3.connect('db.db', check_same_thread=False)
    return thread_local.conn

# Функции для работы с базой данных
def add_item_to_db(item: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO items (item) VALUES (?)", (item,))

def all_ids_list() -> list:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT item FROM items")
        return [int(row[0]) for row in cursor.fetchall()]

def get_all_items() -> list:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM items")
        return cursor.fetchall()

def remove_item_by_id(item_id: int):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))

# Создание таблицы при старте скрипта
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY,
        item TEXT NOT NULL
    )
    ''')
    conn.commit()

# Обработчики сообщений
@app.on_message(filters.me)
def handle_commands(client, message):
    # Обработка команд
    if message.text and message.text.startswith('.'):
        client.delete_messages(message.chat.id, message.id)

        if message.text.startswith('.show'):
            items = get_all_items()
            response = "Содержимое базы данных:\n" + "\n".join(f"{item[0]}. id: {item[1]}" for item in items)
            message.reply_text(response)

        elif message.text.startswith('.add '):
            item = message.text.split(maxsplit=1)[1]
            add_item_to_db(item)
            message.reply_text(f"Добавлен: {item}")

        elif message.text.startswith('.remove '):
            try:
                item_id = int(message.text.split(maxsplit=1)[1])
                remove_item_by_id(item_id)
                message.reply_text(f"Удалено: {item_id}")
            except ValueError:
                message.reply_text("Пожалуйста, укажите корректный ID.")
            except Exception as e:
                message.reply_text(f"Произошла ошибка: {e}")

@app.on_message()
def handle_news(client, message):
    if message.chat.id in all_ids_list():
        client.forward_messages(news_id, message.chat.id, message.id)

# Запуск клиента
app.run()
