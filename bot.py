import os
import telebot
from telebot.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    WebAppInfo
)
import requests
import json
import time
import logging
from threading import Thread
from flask import Flask, jsonify

# ============================================
# КОНФИГУРАЦИЯ И ЛОГГИРОВАНИЕ
# ============================================

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
API_URL = os.environ.get('API_URL')
ADMIN_IDS = os.environ.get('ADMIN_IDS', '723763522')

# Проверка обязательных переменных
if not BOT_TOKEN:
    logger.error("❌ ОШИБКА: BOT_TOKEN не установлен!")
    logger.error("Установите переменную окружения BOT_TOKEN в Render Dashboard")
    exit(1)

if not API_URL:
    logger.error("❌ ОШИБКА: API_URL не установлен!")
    logger.error("Установите переменную окружения API_URL в Render Dashboard")
    exit(1)

# Парсим ID админов
try:
    ADMIN_IDS_LIST = [int(id.strip()) for id in ADMIN_IDS.split(',') if id.strip().isdigit()]
except:
    ADMIN_IDS_LIST = [723763522]  # Fallback
    logger.warning(f"⚠️ Не удалось распарсить ADMIN_IDS, использую fallback: {ADMIN_IDS_LIST}")

logger.info(f"✅ Конфигурация загружена")
logger.info(f"🤖 Бот: ParfumDEPO Bot")
logger.info(f"🌐 API URL: {API_URL[:50]}...")
logger.info(f"👥 Админов: {len(ADMIN_IDS_LIST)}")
logger.info(f"🚀 Запуск на Render.com")

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)

# Состояния для админ-команд
user_states = {}

# ============================================
# WEB SERVER ДЛЯ RENDER HEALTH CHECKS
# ============================================

# Render требует веб-сервер для health checks
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ParfumDEPO Bot</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .status { background: #4CAF50; color: white; padding: 10px 20px; border-radius: 5px; }
            .info { margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>🤖 ParfumDEPO Telegram Bot</h1>
        <div class="status">✅ Статус: <strong>Работает</strong></div>
        
        <div class="info">
            <h3>📊 Информация:</h3>
            <p><strong>Сервис:</strong> Telegram Bot для магазина парфюмерии</p>
            <p><strong>Хостинг:</strong> Render.com</p>
            <p><strong>Статус:</strong> <span style="color: green;">● Online</span></p>
            <p><strong>Время работы:</strong> {:.0f} секунд</p>
            <p><strong>Админов:</strong> {}</p>
        </div>
        
        <div class="info">
            <h3>🔗 Ссылки:</h3>
            <p><a href="/health">Health Check</a> - Проверка состояния</p>
            <p><a href="https://t.me/parfumdepo">Telegram Bot</a> - Написать боту</p>
            <p><a href="https://drochilla2281488.github.io/frontend.github.io/">Магазин</a> - Web App магазин</p>
        </div>
        
        <footer style="margin-top: 40px; border-top: 1px solid #ddd; padding-top: 20px;">
            <p>ParfumDEPO © 2024 | Работает на Render.com</p>
        </footer>
    </body>
    </html>
    """.format(time.time() - start_time, len(ADMIN_IDS_LIST))

@app.route('/health')
def health():
    """Эндпоинт для health check от Render"""
    return jsonify({
        'status': 'healthy',
        'service': 'parfumdepo-telegram-bot',
        'timestamp': time.time(),
        'uptime_seconds': time.time() - start_time,
        'version': '1.0.0',
        'bot_status': 'running',
        'admin_count': len(ADMIN_IDS_LIST)
    }), 200

@app.route('/ping')
def ping():
    """Простой пинг для проверки"""
    return jsonify({'message': 'pong', 'timestamp': time.time()}), 200

def run_flask():
    """Запускает Flask сервер в отдельном потоке"""
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Запуск веб-сервера на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ============================================
# ФУНКЦИИ БОТА (ОСНОВНЫЕ)
# ============================================

def check_if_admin(user_id):
    """Проверяет, является ли пользователь админом"""
    try:
        user_id_int = int(user_id)
        is_admin = user_id_int in ADMIN_IDS_LIST
        return is_admin
    except:
        return False

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    first_name = message.from_user.first_name
    
    logger.info(f"👤 /start от {first_name} (ID: {user_id})")
    
    is_admin = check_if_admin(user_id)
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    web_app_btn = InlineKeyboardButton(
        text="🏪 Открыть магазин",
        web_app=WebAppInfo(url="https://drochilla2281488.github.io/frontend.github.io/")
    )
    
    manager_btn = InlineKeyboardButton(
        text="👨‍💼 Связаться с менеджером",
        url="https://t.me/parfumdepo"
    )
    
    keyboard.add(web_app_btn, manager_btn)
    
    if is_admin:
        admin_btn = InlineKeyboardButton(
            text="⚙️ Админ-панель",
            callback_data="admin_panel"
        )
        keyboard.add(admin_btn)
    
    welcome_text = f"""
🎉 *Добро пожаловать в ParfumDEPO, {first_name}!*{"\n⚙️ *Доступна админ-панель*" if is_admin else ""}

✨ *Возможности:*
• 📦 Полный каталог парфюмерии
• 🔍 Умный поиск и фильтры
• 🛒 Удобная корзина
• 💬 Прямой заказ менеджеру

Нажмите кнопку ниже, чтобы открыть магазин! 👇
"""
    
    bot.send_message(
        chat_id,
        welcome_text,
        parse_mode='Markdown',
        reply_markup=keyboard
    )

@bot.message_handler(commands=['status'])
def bot_status(message):
    """Показывает статус бота"""
    user_id = message.from_user.id
    
    status_text = f"""
📊 *Статус бота ParfumDEPO*

• 🤖 *Бот:* Работает на Render.com
• 🕐 *Аптайм:* {time.time() - start_time:.0f} секунд
• 👥 *Админов:* {len(ADMIN_IDS_LIST)}
• 🌐 *Web App:* [Открыть магазин](https://drochilla2281488.github.io/frontend.github.io/)
• 🔧 *Версия:* 1.0.0

*Ваш ID:* `{user_id}`
*Статус админа:* {'✅ Админ' if check_if_admin(user_id) else '👤 Пользователь'}

Бот работает стабильно! 🚀
"""
    
    bot.reply_to(message, status_text, parse_mode='Markdown', disable_web_page_preview=True)

# ... ВСТАВЬТЕ ВЕСЬ ОСТАЛЬНОЙ КОД БОТА ЗДЕСЬ ...
# (все функции: админ-панель, изменение цен и т.д.)

# ============================================
# ЗАПУСК И УПРАВЛЕНИЕ БОТОМ
# ============================================

def run_bot():
    """Запускает Telegram бота с обработкой ошибок"""
    max_retries = 10
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info("="*60)
            logger.info("🚀 ЗАПУСК ТЕЛЕГРАМ БОТА")
            logger.info(f"🤖 Название: ParfumDEPO Bot")
            logger.info(f"👤 Админов: {len(ADMIN_IDS_LIST)}")
            logger.info(f"🔗 Web App: https://drochilla2281488.github.io/frontend.github.io/")
            logger.info("="*60)
            
            # Получаем информацию о боте
            bot_info = bot.get_me()
            logger.info(f"✅ Бот @{bot_info.username} успешно запущен!")
            
            # Запускаем polling
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
            
        except Exception as e:
            retry_count += 1
            logger.error(f"❌ Ошибка (попытка {retry_count}/{max_retries}): {e}")
            
            if retry_count < max_retries:
                wait_time = 10 * retry_count  # Экспоненциальная задержка
                logger.info(f"🔄 Перезапуск через {wait_time} секунд...")
                time.sleep(wait_time)
            else:
                logger.error(f"💥 Достигнут лимит попыток ({max_retries}). Останавливаюсь.")
                break

# ============================================
# ТОЧКА ВХОДА
# ============================================

if __name__ == "__main__":
    start_time = time.time()
    
    # Запускаем Flask сервер в отдельном потоке
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    logger.info("⏳ Ожидаю запуск веб-сервера...")
    time.sleep(3)  # Даем время Flask запуститься
    
    # Запускаем бота
    try:
        run_bot()
    except KeyboardInterrupt:
        logger.info("👋 Остановка по запросу пользователя...")
    except Exception as e:
        logger.error(f"💀 Непредвиденная ошибка: {e}")
    finally:
        logger.info("✅ Бот остановлен.")
