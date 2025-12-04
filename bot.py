import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from flask import Flask, jsonify
import threading
import logging
import time
import sys

# ============================================
# НАСТРОЙКИ
# ============================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
API_URL = os.environ.get('API_URL')
ADMIN_IDS = [int(x) for x in os.environ.get('ADMIN_IDS', '723763522').split(',') if x]

# Проверка
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не установлен!")
    sys.exit(1)

# Инициализация
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ============================================
# FLASK РОУТЫ (для Render)
# ============================================

@app.route('/')
def home():
    return "🤖 ParfumDEPO Bot работает!"

@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/ping')
def ping():
    return "pong", 200

# ============================================
# КОМАНДЫ БОТА
# ============================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    logger.info(f"👤 /start от {first_name} (ID: {user_id})")
    
    # Проверка админа
    is_admin = user_id in ADMIN_IDS
    
    # Создаем клавиатуру
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
        message.chat.id,
        welcome_text,
        parse_mode='Markdown',
        reply_markup=keyboard
    )

# Простая команда для проверки
@bot.message_handler(commands=['test'])
def test_command(message):
    bot.reply_to(message, "✅ Бот работает на Render!")

@bot.message_handler(commands=['id'])
def get_id(message):
    bot.reply_to(
        message,
        f"👤 Ваш ID: `{message.from_user.id}`\n"
        f"Имя: {message.from_user.first_name}",
        parse_mode='Markdown'
    )

# ============================================
# ЗАПУСК БОТА В ФОНОВОМ РЕЖИМЕ
# ============================================

def run_bot():
    """Запуск бота в фоновом режиме"""
    logger.info("🤖 Запускаю Telegram бота...")
    
    try:
        # Получаем информацию о боте для проверки
        bot_info = bot.get_me()
        logger.info(f"✅ Бот запущен: @{bot_info.username}")
        
        # Запускаем polling с таймаутами
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
        logger.error("Проверьте токен и интернет-соединение")

# ============================================
# ГЛАВНЫЙ ЗАПУСК
# ============================================

if __name__ == "__main__":
    logger.info("="*60)
    logger.info("🚀 PARFUMDEPO BOT - УПРОЩЕННАЯ ВЕРСИЯ ДЛЯ RENDER")
    logger.info("="*60)
    
    # Запускаем бот в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Даем время боту запуститься и вывести логи
    time.sleep(2)
    
    # Запускаем Flask (Render требует веб-сервер)
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Запуск веб-сервера на порту {port}")
    logger.info("="*60)
    
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
