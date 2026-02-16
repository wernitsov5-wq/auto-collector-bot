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
application.add_handler(CommandHandler("drop", auto_collector_bot.drop))
application.add_handler(CommandHandler("garage", auto_collector_bot.garage))
application.add_handler(CommandHandler("collection", auto_collector_bot.collection))
application.add_handler(CommandHandler("top", auto_collector_bot.top))
application.add_handler(CommandHandler("rarity", auto_collector_bot.rarity_info))
application.add_handler(CommandHandler("trade", auto_collector_bot.trade))

# Инициализируем базу данных (Render даст нам постоянное хранилище)
auto_collector_bot.init_database()

# Flask-приложение для приема веб-хуков
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Принимает обновления от Telegram"""
    update = Update.de_json(request.get_json(force=True), application.bot)
    # Запускаем обработку обновления в фоне, чтобы не блокировать ответ Flask
    application.update_queue.put_nowait(update)
    return 'OK', 200

@app.route('/')
def index():
    return 'Бот работает!'

if __name__ == '__main__':
    # Эта часть нужна только для локального запуска

    app.run()

