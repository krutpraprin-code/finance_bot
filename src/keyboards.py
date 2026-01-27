from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from typing import List, Optional

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура"""
    keyboard = [
        ['➕ Добавить расход', '💰 Добавить доход'],
        ['📊 Статистика', '📋 История'],
        ['⚙️ Настройки', 'ℹ️ Помощь']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_categories_keyboard(categories: List[dict], type_: str = 'expense') -> InlineKeyboardMarkup:
    """Клавиатура с категориями"""
    buttons = []
    row = []
    
    for i, category in enumerate(categories):
        if category['type'] == type_:
            button = InlineKeyboardButton(
                f"{category['emoji']} {category['name']}",
                callback_data=f"category_{category['id']}"
            )
            row.append(button)
            
            if len(row) == 2:  # 2 кнопки в ряд
                buttons.append(row)
                row = []
    
    if row:  # Добавляем последний неполный ряд
        buttons.append(row)
    
    # Кнопка "Назад"
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(buttons)

def get_statistics_period_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора периода статистики"""
    buttons = [
        [InlineKeyboardButton("📅 Сегодня", callback_data="stats_today")],
        [InlineKeyboardButton("📅 Неделя", callback_data="stats_week")],
        [InlineKeyboardButton("📅 Месяц", callback_data="stats_month")],
        [InlineKeyboardButton("📅 Год", callback_data="stats_year")],
        [InlineKeyboardButton("📅 Все время", callback_data="stats_all")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения"""
    buttons = [
        [
            InlineKeyboardButton("✅ Да", callback_data="confirm_yes"),
            InlineKeyboardButton("❌ Нет", callback_data="confirm_no")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура настроек"""
    buttons = [
        [InlineKeyboardButton("💰 Валюта", callback_data="settings_currency")],
        [InlineKeyboardButton("🗑️ Очистить данные", callback_data="settings_clear")],
        [InlineKeyboardButton("📤 Экспорт данных", callback_data="settings_export")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_currency_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора валюты"""
    currencies = [
        ("🇷🇺 RUB", "RUB"),
        ("🇺🇸 USD", "USD"),
        ("🇪🇺 EUR", "EUR"),
        ("🇰🇿 KZT", "KZT"),
        ("🇺🇦 UAH", "UAH"),
        ("🇧🇾 BYN", "BYN")
    ]
    
    buttons = []
    row = []
    
    for emoji, code in currencies:
        button = InlineKeyboardButton(f"{emoji} {code}", callback_data=f"currency_{code}")
        row.append(button)
        
        if len(row) == 2:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="settings_back")])
    
    return InlineKeyboardMarkup(buttons)