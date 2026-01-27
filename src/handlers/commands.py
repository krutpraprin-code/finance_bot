import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from src.database import Database
from src.keyboards import get_main_keyboard, get_statistics_period_keyboard, get_settings_keyboard

logger = logging.getLogger(__name__)
db = Database()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Регистрируем/получаем пользователя
    user_data = db.get_or_create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name
    )
    
    # Сохраняем ID пользователя в контексте
    context.user_data['user_id'] = user_data['id']
    
    welcome_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        f"💰 *Финансовый помощник* готов к работе!\n\n"
        f"*Доступные команды:*\n"
        f"• /start - Главное меню\n"
        f"• /add - Добавить операцию\n"
        f"• /stats - Статистика\n"
        f"• /history - История операций\n"
        f"• /export - Экспорт данных\n"
        f"• /help - Помощь\n\n"
        f"*Или используйте кнопки ниже:*"
    )
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )
    
    logger.info(f"👤 Пользователь {user.id} ({user.first_name}) начал работу")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "📚 *Помощь по использованию бота*\n\n"
        "*Основные возможности:*\n"
        "• 📝 Учет расходов и доходов\n"
        "• 📊 Статистика по категориям\n"
        "• 📈 Графики и отчеты\n"
        "• 🔔 Напоминания (в разработке)\n"
        "• 📤 Экспорт данных в CSV\n\n"
        "*Как добавить расход/доход:*\n"
        "1. Нажмите '➕ Добавить расход' или '💰 Добавить доход'\n"
        "2. Выберите категорию\n"
        "3. Введите сумму\n"
        "4. Добавьте описание (необязательно)\n\n"
        "*Для связи с разработчиком:*\n"
        "Если нашли ошибку или есть предложения,\n"
        "пишите: @ваш_username"
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /stats"""
    await update.message.reply_text(
        "📊 *Выберите период для статистики:*",
        parse_mode='Markdown',
        reply_markup=get_statistics_period_keyboard()
    )

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /settings"""
    await update.message.reply_text(
        "⚙️ *Настройки:*",
        parse_mode='Markdown',
        reply_markup=get_settings_keyboard()
    )

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /history"""
    user_id = context.user_data.get('user_id')
    if not user_id:
        await update.message.reply_text("Пожалуйста, сначала отправьте /start")
        return
    
    # Получаем последние 10 транзакций
    transactions = db.get_user_transactions(user_id, limit=10)
    
    if not transactions:
        await update.message.reply_text(
            "📭 У вас пока нет записей.\nДобавьте первую с помощью кнопки '➕ Добавить расход'",
            reply_markup=get_main_keyboard()
        )
        return
    
    message = "📋 *Последние 10 операций:*\n\n"
    total_expenses = 0
    total_income = 0
    
    for t in transactions:
        date = datetime.strptime(t['date'], '%Y-%m-%d %H:%M:%S').strftime('%d.%m %H:%M')
        amount = t['amount']
        type_icon = "➖" if t['type'] == 'expense' else "➕"
        
        if t['type'] == 'expense':
            total_expenses += amount
        else:
            total_income += amount
        
        desc = f"\n   📝 {t['description']}" if t['description'] else ""
        message += f"{type_icon} *{t['category_name']}*: {amount:.2f} руб.\n   📅 {date}{desc}\n\n"
    
    message += f"*Итого:*\n"
    message += f"➖ Расходы: {total_expenses:.2f} руб.\n"
    message += f"➕ Доходы: {total_income:.2f} руб.\n"
    message += f"📊 Баланс: {total_income - total_expenses:.2f} руб."
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )