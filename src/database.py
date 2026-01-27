import sqlite3
import logging
from datetime import datetime
from typing import List, Tuple, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_name: str = 'finance.db'):
        self.db_name = db_name
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для соединения с БД"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def init_database(self):
        """Инициализация базы данных"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Пользователи
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT NOT NULL,
                    language TEXT DEFAULT 'ru',
                    currency TEXT DEFAULT 'RUB',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Категории (общие и пользовательские)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    emoji TEXT NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('expense', 'income')),
                    user_id INTEGER,  -- NULL для общих категорий
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE(name, user_id)
                )
            ''')
            
            # Транзакции
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    category_id INTEGER NOT NULL,
                    amount REAL NOT NULL CHECK(amount > 0),
                    description TEXT,
                    type TEXT NOT NULL CHECK(type IN ('expense', 'income')),
                    date TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
                )
            ''')
            
            # Бюджеты
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    category_id INTEGER,
                    amount REAL NOT NULL,
                    period TEXT NOT NULL CHECK(period IN ('daily', 'weekly', 'monthly')),
                    start_date TIMESTAMP NOT NULL,
                    end_date TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
                )
            ''')
            
            # Создаем индексы для ускорения запросов
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(user_id, date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id)')
            
            # Добавляем стандартные категории, если их нет
            self._create_default_categories(cursor)
            
            logger.info("✅ База данных инициализирована")
    
    def _create_default_categories(self, cursor):
        """Создание стандартных категорий"""
        default_categories = [
            # Расходы
            ('🍔 Еда', 'expense'),
            ('🚌 Транспорт', 'expense'),
            ('🏠 Квартира', 'expense'),
            ('🎮 Развлечения', 'expense'),
            ('👗 Одежда', 'expense'),
            ('💊 Здоровье', 'expense'),
            ('📚 Образование', 'expense'),
            ('🎁 Подарки', 'expense'),
            ('✈️ Путешествия', 'expense'),
            ('🎉 Другое', 'expense'),
            # Доходы
            ('💰 Зарплата', 'income'),
            ('💼 Фриланс', 'income'),
            ('🏦 Инвестиции', 'income'),
            ('🎁 Подарок', 'income'),
            ('💎 Другое', 'income')
        ]
        
        for name, type_ in default_categories:
            emoji, category_name = name.split(' ', 1)
            cursor.execute('''
                INSERT OR IGNORE INTO categories (name, emoji, type, user_id)
                VALUES (?, ?, ?, NULL)
            ''', (category_name, emoji, type_))
    
    # Методы для работы с пользователями
    def get_or_create_user(self, telegram_id: int, username: str, first_name: str) -> dict:
        """Получить или создать пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Проверяем существующего пользователя
            cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
            user = cursor.fetchone()
            
            if user:
                return dict(user)
            
            # Создаем нового пользователя
            cursor.execute('''
                INSERT INTO users (telegram_id, username, first_name)
                VALUES (?, ?, ?)
            ''', (telegram_id, username, first_name))
            
            user_id = cursor.lastrowid
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            return dict(cursor.fetchone())
    
    # Методы для работы с транзакциями
    def add_transaction(self, user_id: int, category_id: int, amount: float, 
                       description: str, type_: str, date: datetime = None) -> int:
        """Добавить транзакцию"""
        if date is None:
            date = datetime.now()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions (user_id, category_id, amount, description, type, date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, category_id, amount, description, type_, date))
            
            return cursor.lastrowid
    
    def get_user_transactions(self, user_id: int, limit: int = 100, 
                             start_date: datetime = None, end_date: datetime = None) -> List[dict]:
        """Получить транзакции пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = '''
                SELECT t.*, c.name as category_name, c.emoji as category_emoji
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.user_id = ?
            '''
            params = [user_id]
            
            if start_date:
                query += ' AND t.date >= ?'
                params.append(start_date)
            
            if end_date:
                query += ' AND t.date <= ?'
                params.append(end_date)
            
            query += ' ORDER BY t.date DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self, user_id: int, start_date: datetime = None, 
                      end_date: datetime = None) -> dict:
        """Получить статистику по пользователю"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Общая статистика
            query = '''
                SELECT 
                    SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expenses,
                    SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
                    COUNT(*) as transaction_count
                FROM transactions 
                WHERE user_id = ?
            '''
            params = [user_id]
            
            if start_date:
                query += ' AND date >= ?'
                params.append(start_date)
            
            if end_date:
                query += ' AND date <= ?'
                params.append(end_date)
            
            cursor.execute(query, params)
            stats = dict(cursor.fetchone() or {})
            
            # Статистика по категориям (только расходы)
            cursor.execute('''
                SELECT c.name, c.emoji, SUM(t.amount) as total
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.user_id = ? AND t.type = 'expense'
                GROUP BY c.id
                ORDER BY total DESC
            ''', (user_id,))
            
            categories = [dict(row) for row in cursor.fetchall()]
            stats['categories'] = categories
            
            return stats
    
    def get_categories(self, user_id: int = None, type_: str = None) -> List[dict]:
        """Получить категории"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT * FROM categories 
                WHERE user_id IS NULL OR user_id = ?
            '''
            params = []
            
            if user_id is not None:
                params.append(user_id)
            
            if type_:
                query += ' AND type = ?'
                params.append(type_)
            
            query += ' ORDER BY type, name'
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]