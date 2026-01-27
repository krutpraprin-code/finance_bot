from datetime import datetime
from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: str
    language: str = 'ru'
    currency: str = 'RUB'
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class Category:
    id: int
    name: str
    emoji: str
    type: str  # 'expense' or 'income'
    user_id: Optional[int] = None  # None для общих категорий

@dataclass
class Transaction:
    id: int
    user_id: int
    category_id: int
    amount: float
    description: Optional[str]
    type: str  # 'expense' or 'income'
    date: datetime
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()