import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from src.database import Database
from src.keyboards import get_main_keyboard

logger = logging.getLogger(__name__)
db = Database()

def format_statistics_message(stats: dict, period: str = "все время") -> str:
    """Форматирование сообщения со статистикой"""
    total_expenses = stats.get('total_expenses') or 0
    total_income = stats.get('total_income') or 0
    transaction_count = stats.get('transaction_count') or 0
    categories = stats.get('categories', [])
    
    message = f"📊 *Статистика за {period}:*\n\n"
    
    # Общая статистика
    message += f"*Общее:*\n"
    message += f"➖ Расходы: {total_expenses:.2f} руб.\n"
    message += f"➕ Доходы: {total_income:.2f} руб.\n"
    message += f"📊 Баланс: {total_income - total_expenses:.2f} руб.\n"
    message += f"📈 Всего операций: {transaction_count}\n\n"
    
    if total_expenses > 0:
        # Статистика по категориям расходов
        message += f"*Расходы по категориям:*\n"
        
        for i, cat in enumerate(categories[:10], 1):  # Только топ-10
            percentage = (cat['total'] / total_expenses) * 100
            bars = "▰" * int(percentage / 5)  # Каждый блок = 5%
            spaces = "▱" * (20 - len(bars))  # Всего 20 символов
            
            message += f"{i}. {cat['emoji']} {cat['name']}\n"
            message += f"   {bars}{spaces} {percentage:5.1f}%\n"
            message += f"   {cat['total']:.2f} руб.\n\n"
    
    if len(categories) > 10:
        message += f"... и еще {len(categories) - 10} категорий\n\n"
    
    # Советы на основе статистики
    if total_expenses > 0:
        savings_rate = ((total_income - total_expenses) / total_income * 100) if total_income > 0 else 0
        
        message += f"*💡 Рекомендации:*\n"
        
        if savings_rate > 20:
            message += "✅ Отличная норма сбережений!\n"
        elif savings_rate > 0:
            message += "⚠️ Норма сбережений низкая. Попробуйте сократить расходы.\n"
        else:
            message += "❌ Вы тратите больше, чем зарабатываете!\n"
        
        # Самая большая категория расходов
        if categories:
            biggest = categories[0]
            message += f"📌 Самые большие расходы: {biggest['emoji']} {biggest['name']} ({biggest['total']:.2f} руб.)"
    
    return message

async def handle_statistics_period(update: Update, context: ContextTypes.DEFAULT_TYPE, period: str):
    """Обработка выбора периода статистики"""
    query = update.callback_query
    await query.answer()
    
    user_id = context.user_data.get('user_id')
    if not user_id:
        await query.edit_message_text("Пожалуйста, сначала отправьте /start")
        return
    
    # Определяем период
    end_date = datetime.now()
    
    if period == 'today':
        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        period_text = "сегодня"
    elif period == 'week':
        start_date = end_date - timedelta(days=7)
        period_text = "неделю"
    elif period == 'month':
        start_date = end_date - timedelta(days=30)
        period_text = "месяц"
    elif period == 'year':
        start_date = end_date - timedelta(days=365)
        period_text = "год"
    else:  # 'all'
        start_date = None
        period_text = "все время"
    
    # Получаем статистику
    stats = db.get_statistics(user_id, start_date, end_date)
    
    if stats['transaction_count'] == 0:
        await query.edit_message_text(
            f"📭 За {period_text} у вас нет записей.\n"
            f"Добавьте первую с помощью кнопки '➕ Добавить расход'",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Формируем и отправляем сообщение
    message = format_statistics_message(stats, period_text)
    
    await query.edit_message_text