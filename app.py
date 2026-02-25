import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
import auto_collector_bot

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Токен берется из переменных окружения (так безопаснее!)
TOKEN = os.environ.get('BOT_TOKEN')
# Создаем приложение бота
application = Application.builder().token(TOKEN).build()

# Инициализируем приложение (это важно!)
import asyncio
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(application.initialize())




application.add_handler(CommandHandler("start", auto_collector_bot.start))
application.add_handler(CommandHandler("test", auto_collector_bot.test))
application.add_handler(CommandHandler("drop", auto_collector_bot.drop))
application.add_handler(CommandHandler("garage", auto_collector_bot.garage))
application.add_handler(CommandHandler("collection", auto_collector_bot.collection))
application.add_handler(CommandHandler("top", auto_collector_bot.top))
application.add_handler(CommandHandler("rarity", auto_collector_bot.rarity_info))
application.add_handler(CommandHandler("trade", auto_collector_bot.trade))
application.add_handler(CommandHandler("setdrop", auto_collector_bot.setdrop))
application.add_handler(CommandHandler("admin_reserves", auto_collector_bot.admin_reserves))


# Flask-приложение для приема веб-хуков
app = Flask(__name__)

# ПРОВЕРКА: обрабатываем обновления напрямую
from telegram.ext import Updater

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        print("🔥 Вебхук вызван!")
        update = Update.de_json(request.get_json(force=True), application.bot)
        print(f"🔥 Получено обновление: {update}")
        
        # СОЗДАЁМ И ЗАПУСКАЕМ EVENT LOOP
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # ЗАПУСКАЕМ ОБРАБОТКУ И ЖДЁМ РЕЗУЛЬТАТ
        loop.run_until_complete(application.process_update(update))
        
        print("🔥 Обработка завершена")
        return 'OK', 200
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        return f'Error: {str(e)}', 500

@app.route('/')
def index():
    return 'Бот работает!'

if __name__ == '__main__':
    # Эта часть нужна только для локального запуска

    app.run()










