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
import threading
from flask import Flask, jsonify
from threading import Thread
import signal
import sys
from dotenv import load_dotenv

# ============================================
# ЗАГРУЗКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ
# ============================================

# Загружаем переменные из .env файла (для разработки)
# В продакшене используем переменные окружения Render
load_dotenv()

# НАСТРОЙКИ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ
# В Render Dashboard добавьте эти переменные:
# BOT_TOKEN, API_URL, ADMIN_IDS
BOT_TOKEN = os.environ.get('BOT_TOKEN')
API_URL = os.environ.get('API_URL')
ADMIN_IDS_STR = os.environ.get('ADMIN_IDS', '')

# ============================================
# ПРОВЕРКА И БЕЗОПАСНАЯ ЗАГРУЗКА
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

# Проверка обязательных переменных
if not BOT_TOKEN:
    logger.error("❌ ОШИБКА: BOT_TOKEN не установлен!")
    logger.error("Добавьте переменную BOT_TOKEN в Render Dashboard")
    logger.error("Или создайте файл .env с BOT_TOKEN=ваш_токен")
    exit(1)

if not API_URL:
    logger.error("❌ ОШИБКА: API_URL не установлен!")
    logger.error("Добавьте переменную API_URL в Render Dashboard")
    exit(1)

# Безопасная загрузка ID админов
ADMIN_IDS = []
if ADMIN_IDS_STR:
    try:
        # Преобразуем строку "123,456,789" в список [123, 456, 789]
        ADMIN_IDS = [int(id.strip()) for id in ADMIN_IDS_STR.split(',') if id.strip().isdigit()]
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки ADMIN_IDS: {e}")
        ADMIN_IDS = []
else:
    logger.warning("⚠️ ADMIN_IDS не установлен. Админ-панель недоступна.")

# Маскируем чувствительные данные для логов
masked_token = f"{BOT_TOKEN[:10]}...{BOT_TOKEN[-5:]}" if BOT_TOKEN else "не установлен"
masked_api_url = f"{API_URL[:30]}...{API_URL[-20:]}" if API_URL else "не установлен"

logger.info(f"✅ Конфигурация загружена")
logger.info(f"🤖 Токен бота: {masked_token}")
logger.info(f"🌐 API URL: {masked_api_url}")
logger.info(f"👥 Админов: {len(ADMIN_IDS)}")

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)

# Состояния для админ-команд
user_states = {}

# Флаг для остановки бота
bot_running = True

# ============================================
# FLASK APP ДЛЯ RENDER HEALTH CHECKS
# ============================================

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
            .status { background: #4CAF50; color: white; padding: 10px 20px; border-radius: 5px; display: inline-block; }
            .warning { background: #ff9800; color: white; padding: 10px 20px; border-radius: 5px; margin: 20px 0; }
            .info { margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 5px; }
            .btn { display: inline-block; padding: 10px 20px; background: #0088cc; color: white; text-decoration: none; border-radius: 5px; margin: 5px; }
        </style>
    </head>
    <body>
        <h1>🤖 ParfumDEPO Telegram Bot</h1>
        <div class="status">✅ Статус: <strong>Работает</strong></div>
        
        <div class="warning">
            ⚠️ <strong>ВНИМАНИЕ:</strong> Этот бот использует безопасную конфигурацию.
            Все секретные данные хранятся в переменных окружения.
        </div>
        
        <div class="info">
            <h3>🔒 Безопасность:</h3>
            <p>✅ Токен бота: защищен переменными окружения</p>
            <p>✅ API ключи: не отображаются в коде</p>
            <p>✅ Данные админов: защищены</p>
            <p>✅ HTTPS: включен автоматически</p>
        </div>
        
        <div class="info">
            <h3>🔗 Ссылки:</h3>
            <p><a class="btn" href="/health">Health Check</a> - Проверка состояния</p>
            <p><a class="btn" href="/ping">Ping</a> - Проверка работы</p>
            <p><a class="btn" href="https://drochilla2281488.github.io/frontend.github.io/">Магазин</a> - Web App магазин</p>
        </div>
        
        <footer style="margin-top: 40px; border-top: 1px solid #ddd; padding-top: 20px;">
            <p>ParfumDEPO © 2024 | 🔒 Безопасная конфигурация</p>
        </footer>
    </body>
    </html>
    """

@app.route('/health')
def health():
    """Эндпоинт для health check от Render"""
    return jsonify({
        'status': 'healthy',
        'service': 'parfumdepo-telegram-bot',
        'security': 'token_hidden',
        'admin_count': len(ADMIN_IDS),
        'version': '2.0.0-secure'
    }), 200

@app.route('/ping')
def ping():
    """Простой пинг для проверки"""
    return jsonify({
        'message': 'pong',
        'timestamp': time.time(),
        'security': 'ok'
    }), 200

# ============================================
# ОСНОВНЫЕ ФУНКЦИИ БОТА (без изменений)
# ============================================

def check_if_admin(user_id):
    """Проверяет, является ли пользователь админом"""
    try:
        user_id_int = int(user_id)
        is_admin = user_id_int in ADMIN_IDS
        logger.info(f"🔍 Проверка админа {user_id}: {is_admin}")
        return is_admin
    except:
        logger.error(f"❌ Ошибка проверки админа для {user_id}")
        return False

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    first_name = message.from_user.first_name
    
    logger.info(f"👤 /start от {first_name} (ID: {user_id})")
    
    is_admin = check_if_admin(user_id)
    
    # Создаем клавиатуру
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Основные кнопки
    web_app_btn = InlineKeyboardButton(
        text="🏪 Открыть магазин",
        web_app=WebAppInfo(url="https://drochilla2281488.github.io/frontend.github.io/")
    )
    
    manager_btn = InlineKeyboardButton(
        text="👨‍💼 Связаться с менеджером",
        url="https://t.me/parfumdepo"
    )
    
    keyboard.add(web_app_btn, manager_btn)
    
    # Если админ - добавляем админ-кнопку
    if is_admin:
        admin_btn = InlineKeyboardButton(
            text="⚙️ Админ-панель",
            callback_data="admin_panel"
        )
        keyboard.add(admin_btn)
    
    # Текст приветствия
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
    
    if is_admin:
        time.sleep(0.5)
        bot.send_message(
            chat_id,
            f"🔐 *Админ-доступ подтвержден!*\n\n"
            f"Ваш ID: `{user_id}`\n"
            f"Для управления ценами нажмите '⚙️ Админ-панель'",
            parse_mode='Markdown'
        )

# ... (ВСТАВЬТЕ ВСЕ ОСТАЛЬНЫЕ ФУНКЦИИ БОТА ЗДЕСЬ)
# Админ-панель, изменение цен, добавление админов и т.д.
# Код функций без изменений, только удалите хардкодные значения

# ============================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ============================================

if __name__ == "__main__":
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("="*60)
    logger.info("🚀 ЗАПУСК PARFUMDEPO TELEGRAM BOT (БЕЗОПАСНЫЙ)")
    logger.info("="*60)
    
    try:
        bot_info = bot.get_me()
        logger.info(f"🤖 Бот: @{bot_info.username}")
    except Exception as e:
        logger.error(f"❌ Не удалось подключиться к боту: {e}")
        logger.error("Проверьте BOT_TOKEN в переменных окружения")
        exit(1)
    
    logger.info(f"👥 Админов: {len(ADMIN_IDS)}")
    logger.info(f"🌐 Web App: https://drochilla2281488.github.io/frontend.github.io/")
    logger.info(f"🔒 Конфигурация: БЕЗОПАСНАЯ (переменные окружения)")
    logger.info("="*60)
    
    # Запускаем бота в отдельном потоке
    bot_thread = Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask приложение
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Запуск Flask сервера на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
