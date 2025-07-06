import sqlite3
import os

# Path to local database file
DB_PATH = "dalTadka.db"

def connect_db():
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")  # Enable write-ahead logging
    return conn

def create_tables():
    conn = connect_db()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_id TEXT,
            cloudinary_url TEXT,      -- ✅ NEW: for storing image URL
            photographer_email TEXT,
            timestamp TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS encodings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            photo_id INTEGER,
            encoding TEXT,
            FOREIGN KEY(photo_id) REFERENCES photos(id)
        )
    ''')

    conn.commit()
    conn.close()


def get_all_encodings():
    conn = connect_db()
    try:
        c = conn.cursor()
        c.execute('''
            SELECT e.encoding, p.cloudinary_url
            FROM encodings e
            JOIN photos p ON e.photo_id = p.id
        ''')
        results = c.fetchall()
        return [{"encoding": row[0], "cloudinary_url": row[1]} for row in results]
    finally:
        conn.close()

def delete_all_user_photos(email):
    conn = connect_db()
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM photos WHERE photographer_email = ?", (email,))
        photos = c.fetchall()

        photo_ids = [row[0] for row in photos]
        c.executemany("DELETE FROM encodings WHERE photo_id = ?", [(pid,) for pid in photo_ids])
        c.execute("DELETE FROM photos WHERE photographer_email = ?", (email,))

        conn.commit()
    finally:
        conn.close()

def delete_all_photos():
    conn = connect_db()
    try:
        c = conn.cursor()
        # Local path column no longer exists; skip file deletion
        pass


        c.execute("DELETE FROM encodings")
        c.execute("DELETE FROM photos")
        conn.commit()
    finally:
        conn.close()
