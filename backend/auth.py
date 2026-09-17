import sqlite3
import hashlib
import os

class AuthManager:
    def __init__(self, master_db_path="master_auth.db"):
        self.db_path = master_db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    db_filename TEXT NOT NULL
                )
            ''')
            conn.commit()

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def signup(self, username, password):
        username = username.strip().lower()
        if not username or not password:
            return False, "Username and password cannot be empty."
            
        hashed_pw = self._hash_password(password)
        db_filename = f"wallet_{username}.db"
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password_hash, db_filename) VALUES (?, ?, ?)",
                    (username, hashed_pw, db_filename)
                )
                conn.commit()
            return True, db_filename
        except sqlite3.IntegrityError:
            return False, "Username already exists."

    def get_all_users(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users ORDER BY username ASC")
            return [row[0] for row in cursor.fetchall()]

    def change_password(self, username, old_password, new_password):
        username = username.strip().lower()
        old_hashed = self._hash_password(old_password)
        new_hashed = self._hash_password(new_password)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ? AND password_hash = ?", (username, old_hashed))
            if not cursor.fetchone():
                return False, "Incorrect old password."
                
            cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (new_hashed, username))
            conn.commit()
            return True, "Password updated successfully!"

    def login(self, username, password):
        username = username.strip().lower()
        hashed_pw = self._hash_password(password)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT db_filename FROM users WHERE username = ? AND password_hash = ?", (username, hashed_pw))
            result = cursor.fetchone()
            
            if result:
                return True, result[0]
            return False, "Invalid username or password."
