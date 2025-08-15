import sqlite3
import os

def create_table():
    db_path = "../../database/database.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_name TEXT NOT NULL,
            created_at TEXT,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            UNIQUE(topic_name, user_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS words (
            word_id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_name TEXT NOT NULL UNIQUE,
            word_meaning TEXT NOT NULL,
            part_of_speech TEXT NOT NULL,
            phonetic TEXT NOT NULL,
            definition TEXT NOT NULL,
            example TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topic_word (
            topic_id INTEGER,
            word_id INTEGER,
            PRIMARY KEY(topic_id, word_id),
            FOREIGN KEY(topic_id) REFERENCES topics(topic_id),
            FOREIGN KEY(word_id) REFERENCES words(word_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_word_progress (
            user_id INTEGER,
            topic_id INTEGER,
            word_id INTEGER,
            PRIMARY KEY(user_id, word_id),
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            FOREIGN KEY(word_id) REFERENCES words(word_id)
        )
    """)

    conn.commit()
    conn.close()

    print("Tables created successfully.")

if __name__ == "__main__":
    create_table()