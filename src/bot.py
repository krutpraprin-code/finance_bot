import os
import sys
import logging
from dotenv import load_dotenv

# Добавляем src в путь Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загружаем переменные
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

if not TOKEN:
    logger.error("❌ Токен не найден!")
    exit(1)

try:
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        CallbackQueryHandler,
        ConversationHandler,
        filters,
        ContextTypes
    )
    
    # Относительные импорты (без src!)
    from handlers.commands import (
        start_command, help_command, stats_command,
        settings_command, history_command
    )
    from handlers.expenses import (
        start_add_transaction, category_selected,
        amount_received, description_received, cancel,
        SELECTING_CATEGORY, ENTERING_AMOUNT, ENTERING_DESCRIPTION
    )
    from handlers.statistics import handle_statistics_period, back_to_main
    
    from keyboards import get_main_keyboard
    
except ImportError as e:
    logger.error(f"❌ Ошибка импорта: {e}")
    exit(1)

def main():
    logger.info("=" * 50)
    logger.info("🚀 ЗАПУСК ФИНАНСОВОГО БОТА")
    logger.info(f"Токен: {TOKEN[:10]}...")
    logger.info("=" * 50)
    
    try:
        app = Application.builder().token(TOKEN).build()
        
        # Команды
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("stats", stats_command))
        app.add_handler(CommandHandler("history", history_command))
        
        # Conversation handlers
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
        
        app.add_handler(conv_expense)
        
        # Callback handlers
        app.add_handler(CallbackQueryHandler(
            lambda u, c: handle_statistics_period(u, c, 'today'),
            pattern='^stats_today$'
        ))
        app.add_handler(CallbackQueryHandler(back_to_main, pattern='^back_to_main$'))
        
        logger.info("✅ Бот запущен и готов к работе!")
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    main()