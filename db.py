import sqlite3
import os

DB_NAME = "production.db"


def create_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)

def initialize_database():
    """Создание таблицы, если она еще не существует."""
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clothing_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        articul TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        size TEXT NOT NULL,
        date_added TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        cost REAL NOT NULL,
        price REAL NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )    
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    """)

    conn.commit()
    conn.close()

def execute_query(query, params=()):
    """Выполняет запрос к базе данных."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()

def fetch_all(query, params=()):
    """Получает данные из базы данных."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

roles = ('Пользователь', "Администратор")


def seed_database():
    conn = create_connection()
    cursor = conn.cursor()

    conn.commit()

    conn.close()

    print("База данных заполнена")


def fetch_sales_by_category():
    query = """
    SELECT category, SUM(quantity) 
    FROM clothing_items 
    GROUP BY category
    """
    result = execute_query(query)
    print(result)
    if not result:
        return None
    categories, sales = zip(*result)
    return categories, sales

def fetch_analytics_data():
    query = """
    SELECT category, SUM(quantity) AS total_sales, 
           SUM(price * quantity - cost * quantity) AS profit
    FROM clothing_items 
    GROUP BY category
    """
    return execute_query(query)