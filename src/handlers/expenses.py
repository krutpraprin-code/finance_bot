import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from src.database import Database
from src.keyboards import get_categories_keyboard, get_main_keyboard

logger = logging.getLogger(__name__)
db = Database()

# Состояния ConversationHandler
SELECTING_CATEGORY, ENTERING_AMOUNT, ENTERING_DESCRIPTION = range(3)

async def start_add_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE, type_: str = 'expense'):
    """Начало добавления транзакции"""
    user_id = context.user_data.get('user_id')
    if not user_id:
        await update.message.reply_text("Пожалуйста, сначала отправьте /start")
        return ConversationHandler.END
    
    context.user_data['transaction_type'] = type_
    
    # Получаем категории
    categories = db.get_categories(user_id=user_id, type_=type_)
    
    type_text = "расход" if type_ == 'expense' else "доход"
    await update.message.reply_text(
        f"Выберите категорию для {type_text}a:",
        reply_markup=get_categories_keyboard(categories, type_)
    )
    
    return SELECTING_CATEGORY

async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора категории"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'back_to_main':
        await query.edit_message_text(
            "Возвращаемся в главное меню...",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    category_id = int(query.data.replace('category_', ''))
    context.user_data['category_id'] = category_id
    
    type_ = context.user_data.get('transaction_type', 'expense')
    type_text = "расход" if type_ == 'expense' else "доход"
    
    await query.edit_message_text(
        f"Введите сумму {type_text}a (только цифры):\n\n"
        f"*Пример:* 500.50",
        parse_mode='Markdown'
    )
    
    return ENTERING_AMOUNT

async def amount_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка введенной суммы"""
    try:
        amount = float(update.message.text.replace(',', '.'))
        
        if amount <= 0:
            await update.message.reply_text("❌ Сумма должна быть больше 0!")
            return ENTERING_AMOUNT
        
        context.user_data['amount'] = amount
        
        type_ = context.user_data.get('transaction_type', 'expense')
        type_text = "расход" if type_ == 'expense' else "доход"
        
        await update.message.reply_text(
            f"Введите описание {type_text}a (или отправьте '-' для пропуска):\n\n"
            f"*Пример:* Обед в кафе",
            parse_mode='Markdown'
        )
        
        return ENTERING_DESCRIPTION
        
    except ValueError:
        await update.message.reply_text(
            "❌ Пожалуйста, введите число!\n\n"
            "*Пример:* 500.50",
            parse_mode='Markdown'
        )
        return ENTERING_AMOUNT

async def description_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка описания и сохранение транзакции"""
    description = update.message.text.strip()
    if description == '-':
        description = ''
    
    user_id = context.user_data['user_id']
    category_id = context.user_data['category_id']
    amount = context.user_data['amount']
    type_ = context.user_data.get('transaction_type', 'expense')
    
    try:
        # Сохраняем транзакцию
        transaction_id = db.add_transaction(
            user_id=user_id,
            category_id=category_id,
            amount=amount,
            description=description,
            type_=type_
        )
        
        # Получаем информацию о категории
        categories = db.get_categories(user_id=user_id)
        category = next((c for c in categories if c['id'] == category_id), None)
        
        type_text = "расход" if type_ == 'expense' else "доход"
        type_icon = "➖" if type_ == 'expense' else "➕"
        
        message = (
            f"✅ {type_icon} *{type_text.capitalize()} сохранен!*\n\n"
            f"*Категория:* {category['emoji']} {category['name']}\n"
            f"*Сумма:* {amount:.2f} руб.\n"
        )
        
        if description:
            message += f"*Описание:* {description}\n"
        
        message += f"\nID записи: #{transaction_id}"
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        
        logger.info(f"💾 Сохранен {type_text}: {amount} руб. (user: {user_id})")
        
        # Очищаем временные данные
        context.user_data.pop('transaction_type', None)
        context.user_data.pop('category_id', None)
        context.user_data.pop('amount', None)
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Ошибка сохранения транзакции: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при сохранении. Попробуйте еще раз.",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена добавления транзакции"""
    await update.message.reply_text(
        "❌ Добавление отменено.",
        reply_markup=get_main_keyboard()
    )
    
    # Очищаем временные данные
    context.user_data.pop('transaction_type', None)
    context.user_data.pop('category_id', None)
    context.user_data.pop('amount', None)
    
    return ConversationHandler.END