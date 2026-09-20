import sqlite3
import os
import json
from datetime import datetime
import collections
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path="finance_wallet.db"):
        self.app_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        os.makedirs(self.app_dir, exist_ok=True)
        if os.path.isabs(db_path):
            self.db_path = db_path
        else:
            self.db_path = os.path.join(self.app_dir, db_path)
        self._init_db()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row # To access columns by name
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initializes the database schema if it doesn't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Categories Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('Income', 'Expense')),
                    color_hex TEXT
                )
            ''')
            
            # 2. Transactions Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL DEFAULT 'Transaction',
                    amount REAL NOT NULL,
                    date TEXT NOT NULL,
                    description TEXT,
                    category_id INTEGER,
                    is_recurring BOOLEAN NOT NULL DEFAULT 0,
                    recurrence_period TEXT,
                    transaction_author TEXT,
                    is_deleted BOOLEAN NOT NULL DEFAULT 0,
                    FOREIGN KEY (category_id) REFERENCES categories (id)
                )
            ''')
            
            # 2.5 Transaction History Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transaction_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id INTEGER,
                    updated_at TEXT NOT NULL,
                    changes TEXT NOT NULL,
                    FOREIGN KEY (transaction_id) REFERENCES transactions (id)
                )
            ''')
            
            # 3. Saving Goals Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS saving_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    target_amount REAL NOT NULL,
                    current_amount REAL NOT NULL DEFAULT 0.0,
                    deadline TEXT
                )
            ''')
            
            # 3.5 Saving Contributions Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS saving_contributions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    date TEXT NOT NULL,
                    description TEXT,
                    FOREIGN KEY (goal_id) REFERENCES saving_goals (id)
                )
            ''')
            
            # 4. Settings Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            ''')
            
            conn.commit()
        self._upgrade_db()

    def _upgrade_db(self):
        """Safely applies schema migrations to existing databases."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Add 'tags' to transactions
            cursor.execute("PRAGMA table_info(transactions)")
            tx_cols = [row[1] for row in cursor.fetchall()]
            if 'tags' not in tx_cols:
                cursor.execute("ALTER TABLE transactions ADD COLUMN tags TEXT")
                
            # Add 'budget_limit' to categories
            cursor.execute("PRAGMA table_info(categories)")
            cat_cols = [row[1] for row in cursor.fetchall()]
            if 'budget_limit' not in cat_cols:
                cursor.execute("ALTER TABLE categories ADD COLUMN budget_limit REAL")
                
            conn.commit()

    # --- CATEGORY CRUD ---

    def add_category(self, name, cat_type, color_hex="", budget_limit=0.0):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO categories (name, type, color_hex, budget_limit) VALUES (?, ?, ?, ?)",
                (name, cat_type, color_hex, budget_limit)
            )
            conn.commit()
            return cursor.lastrowid

    def get_categories(self, cat_type=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if cat_type:
                cursor.execute("SELECT * FROM categories WHERE type = ?", (cat_type,))
            else:
                cursor.execute("SELECT * FROM categories")
            return [dict(row) for row in cursor.fetchall()]

    def update_category(self, category_id, name=None, cat_type=None, color_hex=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Fetch existing to only update provided fields
            cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
            current = cursor.fetchone()
            if not current:
                return False
            
            new_name = name if name is not None else current['name']
            new_type = cat_type if cat_type is not None else current['type']
            new_color = color_hex if color_hex is not None else current['color_hex']
            
            cursor.execute(
                "UPDATE categories SET name = ?, type = ?, color_hex = ? WHERE id = ?",
                (new_name, new_type, new_color, category_id)
            )
            conn.commit()
            return True

    def delete_category(self, category_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # We could also handle re-assigning transactions for this category to a 'default' category here later
            cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            conn.commit()
            return cursor.rowcount > 0

    # --- TRANSACTION CRUD ---

    def add_transaction(self, name, amount, date, description, category_id, is_recurring=False, recurrence_period=None, transaction_author="", tags=""):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO transactions 
                   (name, amount, date, description, category_id, is_recurring, recurrence_period, transaction_author, tags) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (name, amount, date, description, category_id, is_recurring, recurrence_period, transaction_author, tags)
            )
            conn.commit()
            return cursor.lastrowid

    def get_transactions(self, start_date=None, end_date=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM transactions WHERE is_deleted = 0"
            params = []
            
            if start_date and end_date:
                query += " AND date >= ? AND date <= ?"
                params.extend([start_date, end_date])
            elif start_date:
                query += " AND date >= ?"
                params.append(start_date)
            elif end_date:
                query += " AND date <= ?"
                params.append(end_date)
                
            query += " ORDER BY date DESC"
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def update_transaction(self, transaction_id, **kwargs):
        from datetime import datetime
        import json
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions WHERE id = ? AND is_deleted = 0", (transaction_id,))
            current = cursor.fetchone()
            if not current:
                return False

            updates = []
            params = []
            changes = {}
            for key, value in kwargs.items():
                if key in current.keys() and current[key] != value:
                    updates.append(f"{key} = ?")
                    params.append(value)
                    changes[key] = {'from': current[key], 'to': value}
            
            if not updates:
                return True
                
            # Log history
            updated_at = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO transaction_history (transaction_id, updated_at, changes) VALUES (?, ?, ?)",
                (transaction_id, updated_at, json.dumps(changes))
            )
                
            params.append(transaction_id)
            query = f"UPDATE transactions SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            return True

    def delete_transaction(self, transaction_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE transactions SET is_deleted = 1 WHERE id = ?", (transaction_id,))
            conn.commit()
            return cursor.rowcount > 0

    # --- SAVING GOALS CRUD ---

    def add_goal(self, name, target_amount, current_amount=0.0, deadline=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO saving_goals (name, target_amount, current_amount, deadline) VALUES (?, ?, ?, ?)",
                (name, target_amount, current_amount, deadline)
            )
            conn.commit()
            return cursor.lastrowid

    def get_goals(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM saving_goals ORDER BY deadline ASC")
            return [dict(row) for row in cursor.fetchall()]

    def update_goal(self, goal_id, **kwargs):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM saving_goals WHERE id = ?", (goal_id,))
            current = cursor.fetchone()
            if not current:
                return False

            updates = []
            params = []
            for key, value in kwargs.items():
                if key in current.keys():
                    updates.append(f"{key} = ?")
                    params.append(value)
            
            if not updates:
                return True
                
            params.append(goal_id)
            query = f"UPDATE saving_goals SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            return True

    def add_goal_contribution(self, goal_id, amount, date, description=""):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # 1. Insert into history
            cursor.execute(
                "INSERT INTO saving_contributions (goal_id, amount, date, description) VALUES (?, ?, ?, ?)",
                (goal_id, amount, date, description)
            )
            # 2. Update current amount
            cursor.execute("UPDATE saving_goals SET current_amount = current_amount + ? WHERE id = ?", (amount, goal_id))
            conn.commit()
            return cursor.lastrowid
            
    def get_goal_contributions(self, goal_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM saving_contributions WHERE goal_id = ? ORDER BY date DESC", (goal_id,))
            return [dict(row) for row in cursor.fetchall()]

    def delete_goal(self, goal_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM saving_goals WHERE id = ?", (goal_id,))
            conn.commit()
            return cursor.rowcount > 0

    # --- SETTINGS CRUD ---
    def set_setting(self, key, value):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
            conn.commit()

    def get_setting(self, key, default=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return row['value']
            return default

    # --- DATA AGGREGATION ---

    def get_total_balance(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Join transactions with categories to determine Income vs Expense
            query = """
                SELECT 
                    SUM(CASE WHEN c.type = 'Income' THEN t.amount ELSE 0 END) as total_income,
                    SUM(CASE WHEN c.type = 'Expense' THEN t.amount ELSE 0 END) as total_expense
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.is_deleted = 0
            """
            cursor.execute(query)
            row = cursor.fetchone()
            income = row['total_income'] if row['total_income'] else 0.0
            expense = row['total_expense'] if row['total_expense'] else 0.0
            return income - expense

    def get_expenses_by_category(self, start_date=None, end_date=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT c.name, c.color_hex, SUM(t.amount) as total
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE c.type = 'Expense' AND t.is_deleted = 0
            """
            params = []
            
            if start_date and end_date:
                query += " AND t.date >= ? AND t.date <= ?"
                params.extend([start_date, end_date])
            elif start_date:
                query += " AND t.date >= ?"
                params.append(start_date)
            elif end_date:
                query += " AND t.date <= ?"
                params.append(end_date)
                
            query += " GROUP BY c.id ORDER BY total DESC"
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_income_vs_expense(self, start_date=None, end_date=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT c.type, SUM(t.amount) as total
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.is_deleted = 0
            """
            params = []
            
            if start_date and end_date:
                query += " AND t.date >= ? AND t.date <= ?"
                params.extend([start_date, end_date])
            elif start_date:
                query += " AND t.date >= ?"
                params.append(start_date)
            elif end_date:
                query += " AND t.date <= ?"
                params.append(end_date)
                
            query += " GROUP BY c.type"
            cursor.execute(query, params)
            results = {'Income': 0.0, 'Expense': 0.0}
            for row in cursor.fetchall():
                results[row['type']] = row['total'] if row['total'] else 0.0
            return results

if __name__ == "__main__":
    db = DatabaseManager("test_finance_wallet.db")
    print("Database initialized successfully.")
