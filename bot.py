from pyrogram import Client, filters
import configparser
import sqlite3
import threading

config = configparser.ConfigParser()
config.read('config.ini')

api_id = config['DATA']['api_id']
api_hash = config['DATA']['api_hash']
news_id = config['DATA']['news']

thread_local = threading.local()

def get_db_connection():
    if not hasattr(thread_local, "conn"):
        thread_local.conn = sqlite3.connect('db.db', check_same_thread=False)
    return thread_local.conn

def add_item_to_db(item):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO items (item) VALUES (?)", (item,))

def all_ids_list():
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT item FROM items")
        ids = [int(row[0]) for row in cursor.fetchall()]
    return ids

def get_all_items():
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM items")
        return cursor.fetchall()

def remove_item_by_id(item_id):
    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))

with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY,
        item TEXT NOT NULL
    )
    ''')
    conn.commit()

app = Client("my_account", api_id=api_id, api_hash=api_hash)

@app.on_message(filters.me)
def handle_commands(client, message):
    if message.text is None or not message.text.startswith('.'):
        return

    client.delete_messages(message.chat.id, message.id)

    if message.text.startswith('.show'):
        items = get_all_items()
        response = "Содержимое базы данных:\n"
        for item in items:
            response += f"{item[0]}. id: {item[1]}\n"
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
    chat_id = message.chat.id
    ids_list = all_ids_list()
    if chat_id in ids_list:
        print("Gotcha!")
        client.forward_messages(news_id, message.chat.id, message.id)

app.run()
