import os
import logging
from dotenv import load_dotenv
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters
)

from src.handlers.commands import (
    start_command, help_command, stats_command,
    settings_command, history_command
)
from src.handlers.expenses import (
    start_add_transaction, category_selected,
    amount_received, description_received, cancel,
    SELECTING_CATEGORY, ENTERING_AMOUNT, ENTERING_DESCRIPTION
)
from src.handlers.statistics import handle_statistics_period, back_to_main
from src.keyboards import get_main_keyboard

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получение токена
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    logger.error("❌ BOT_TOKEN не найден в переменных окружения!")
    logger.error("Установите переменную BOT_TOKEN в Railway или в файле .env")
    exit(1)

def main():
    """Главная функция запуска бота"""
    logger.info("=" * 50)
    logger.info("🚀 ЗАПУСК ФИНАНСОВОГО БОТА")
    logger.info(f"Токен: {TOKEN[:10]}...")
    logger.info("=" * 50)
    
    try:
        # Создаем приложение
        app = Application.builder().token(TOKEN).build()
        
        # ConversationHandler для добавления расходов
        conv_expense = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex('^➕ Добавить расход$'), 
                             lambda u, c: start_add_transaction(u, c, 'expense'))
            ],
            states={
                SELECTING_CATEGORY: [CallbackQueryHandler(category_selected)],
                ENTERING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount_received)],
                ENTERING_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description_received)]
            },
            fallbacks=[CommandHandler('cancel', cancel)]
        )
        
        # ConversationHandler для добавления доходов
        conv_income = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex('^💰 Добавить доход$'), 
                             lambda u, c: start_add_transaction(u, c, 'income'))
            ],
            states={
                SELECTING_CATEGORY: [CallbackQueryHandler(category_selected)],
                ENTERING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount_received)],
                ENTERING_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description_received)]
            },
            fallbacks=[CommandHandler('cancel', cancel)]
        )
        
        # Обработчики команд
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("stats", stats_command))
        app.add_handler(CommandHandler("settings", settings_command))
        app.add_handler(CommandHandler("history", history_command))
        
        # Добавляем ConversationHandlers
        app.add_handler(conv_expense)
        app.add_handler(conv_income)
        
        # Обработчики callback-запросов (статистика)
        app.add_handler(CallbackQueryHandler(
            lambda u, c: handle_statistics_period(u, c, 'today'),
            pattern='^stats_today$'
        ))
        app.add_handler(CallbackQueryHandler(
            lambda u, c: handle_statistics_period(u, c, 'week'),
            pattern='^stats_week$'
        ))
        app.add_handler(CallbackQueryHandler(
            lambda u, c: handle_statistics_period(u, c, 'month'),
            pattern='^stats_month$'
        ))
        app.add_handler(CallbackQueryHandler(
            lambda u, c: handle_statistics_period(u, c, 'year'),
            pattern='^stats_year$'
        ))
        app.add_handler(CallbackQueryHandler(
            lambda u, c: handle_statistics_period(u, c, 'all'),
            pattern='^stats_all$'
        ))
        app.add_handler(CallbackQueryHandler(back_to_main, pattern='^back_to_main$'))
        
        # Обработчик текстовых сообщений (для главного меню)
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            lambda update, context: update.message.reply_text(
                "Используйте кнопки меню 👇",
                reply_markup=get_main_keyboard()
            )
        ))
        
        # Запуск бота
        logger.info("✅ Бот запущен и готов к работе!")
        logger.info("📱 Найдите бота в Telegram и отправьте /start")
        logger.info("=" * 50)
        
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query']
        )
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise
    finally:
        logger.info("🛑 Бот остановлен")

if __name__ == '__main__':
    main()