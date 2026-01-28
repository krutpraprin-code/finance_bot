import os
import logging
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем токен
TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    logger.error("❌ Токен не найден!")
    exit(1)

# Простой HTTP сервер для healthcheck
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Отключаем логи запросов
        pass

def start_health_server():
    """Запускает простой HTTP сервер для healthcheck"""
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    logger.info(f"🌐 Health server started on port {port}")
    server.serve_forever()

def main():
    logger.info("=" * 50)
    logger.info("🚀 ЗАПУСК ФИНАНСОВОГО БОТА")
    logger.info(f"Токен: {TOKEN[:10]}...")
    logger.info("=" * 50)
    
    try:
        # Импортируем здесь, чтобы видеть ошибки импорта
        from telegram.ext import Application, CommandHandler
        
        # Запускаем health сервер в отдельном потоке
        health_thread = Thread(target=start_health_server, daemon=True)
        health_thread.start()
        
        # Простая команда для теста
        async def start(update, context):
            await update.message.reply_text("✅ Бот работает на Railway!")
        
        # Создаем приложение бота
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        
        logger.info("✅ Бот запущен и готов к работе!")
        logger.info("📱 Откройте Telegram и отправьте /start")
        
        # Запускаем бота
        app.run_polling(drop_pending_updates=True)
        
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта: {e}")
        logger.error("Установите библиотеки: pip install python-telegram-bot")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        logger.info("🛑 Бот остановлен")

if __name__ == '__main__':
    main()