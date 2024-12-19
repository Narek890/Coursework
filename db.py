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
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clothing_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        articul TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        size TEXT NOT NULL,
        date_added TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        cost REAL NOT NULL,
        price REAL NOT NULL,
        category_id INTEGER NOT NULL,
        material_id TEXT NOT NULL,
        FOREIGN KEY (category_id) REFERENCES categories (id)
        )  
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('user', 'admin', 'employee')) DEFAULT 'user'
    )    
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS materials (
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

    # Сидирование категорий
    categories = [
        ('Одежда',),
        ('Обувь',),
        ('Аксессуары',)
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO categories (name) VALUES (?)
    """, categories)

    # Сидирование пользователей
    users = [
        ('Admin', 'strongpass', 'admin')
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)
    """, users)

    # Сидирование материалов
    materials = [
        ('Ткань',),
        ('Хлопок',),
        ('Кожа',),
        ('Мех',)
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO materials (name) VALUES (?)
    """, materials)

    # Сидирование предметов одежды
    clothing_items = [
        ('12345', 'Футболка', 'M', 1, '2023-08-01', 10, 19.99, 29.99, 1),
        ('67890', 'Джинсы', 'L', 2, '2023-08-02', 5, 24.99, 34.99, 1),
        ('54321', 'Костюм', 'XS', 3, '2023-08-03', 20, 39.99, 49.99, 1)
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO clothing_items 
        (articul, name, size, material_id, date_added, quantity, cost, price, category_id) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, clothing_items)

    conn.commit()
    conn.close()

    print("База данных успешно сидирована")
