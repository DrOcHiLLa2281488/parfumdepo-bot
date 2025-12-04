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
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8323054941:AAEF9FTsXt9ubzwXyTrqCcZ0Zrxs_iGpYUE')
API_URL = os.environ.get('API_URL', 'https://script.google.com/macros/s/AKfycbwC2rYV5q4zOyZ7EVoAzQIwigeTAi9bTelTYQ8cmdb_A7CMkJIkT2ajZNFF-fl9YxVjeQ/exec')
ADMIN_IDS_ENV = os.environ.get('ADMIN_IDS', '723763522,1184242607,7450272065,840550982')

# Проверка обязательных переменных
if not BOT_TOKEN or BOT_TOKEN == 'ВАШ_ТОКЕН_ЗДЕСЬ':
    logger.error("❌ ОШИБКА: BOT_TOKEN не установлен!")
    logger.error("Установите переменную окружения BOT_TOKEN в Render Dashboard")
    exit(1)

# Парсим ID админов
try:
    ADMIN_IDS = [int(id.strip()) for id in ADMIN_IDS_ENV.split(',') if id.strip().isdigit()]
except:
    ADMIN_IDS = [723763522, 1184242607, 7450272065, 840550982]  # Fallback
    logger.warning(f"⚠️ Не удалось распарсить ADMIN_IDS, использую fallback: {ADMIN_IDS}")

logger.info(f"✅ Конфигурация загружена")
logger.info(f"🤖 Бот: ParfumDEPO Bot")
logger.info(f"🌐 API URL: {API_URL[:50]}...")
logger.info(f"👥 Админов: {len(ADMIN_IDS)}")
logger.info(f"🚀 Запуск на Render.com")

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
            .info { margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 5px; }
            .btn { display: inline-block; padding: 10px 20px; background: #0088cc; color: white; text-decoration: none; border-radius: 5px; margin: 5px; }
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
            <p><strong>Админов:</strong> {}</p>
        </div>
        
        <div class="info">
            <h3>🔗 Ссылки:</h3>
            <p><a class="btn" href="/health">Health Check</a> - Проверка состояния</p>
            <p><a class="btn" href="https://t.me/parfumdepo">Telegram Bot</a> - Написать боту</p>
            <p><a class="btn" href="https://drochilla2281488.github.io/frontend.github.io/">Магазин</a> - Web App магазин</p>
        </div>
        
        <footer style="margin-top: 40px; border-top: 1px solid #ddd; padding-top: 20px;">
            <p>ParfumDEPO © 2024 | Работает на Render.com</p>
        </footer>
    </body>
    </html>
    """.format(len(ADMIN_IDS))

@app.route('/health')
def health():
    """Эндпоинт для health check от Render"""
    return jsonify({
        'status': 'healthy',
        'service': 'parfumdepo-telegram-bot',
        'bot_status': 'running' if bot else 'stopped',
        'admin_count': len(ADMIN_IDS),
        'version': '2.0.0'
    }), 200

@app.route('/ping')
def ping():
    """Простой пинг для проверки"""
    return jsonify({'message': 'pong', 'timestamp': time.time()}), 200

# ============================================
# ФУНКЦИИ БОТА
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

# ============================================
# ОСНОВНЫЕ КОМАНДЫ
# ============================================

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
    
    # Отправляем сообщение
    bot.send_message(
        chat_id,
        welcome_text,
        parse_mode='Markdown',
        reply_markup=keyboard
    )
    
    # Дополнительное сообщение для админов
    if is_admin:
        time.sleep(0.5)
        bot.send_message(
            chat_id,
            f"🔐 *Админ-доступ подтвержден!*\n\n"
            f"Ваш ID: `{user_id}`\n"
            f"Для управления ценами нажмите '⚙️ Админ-панель'\n\n"
            f"*Быстрые команды:*\n"
            f"• /admin - открыть админ-панель\n"
            f"• /changeprice - изменить цены\n"
            f"• /addadmin - добавить админа",
            parse_mode='Markdown'
        )
    
    # Сбрасываем состояние пользователя
    if user_id in user_states:
        del user_states[user_id]

# ============================================
# АДМИН-ПАНЕЛЬ
# ============================================

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def show_admin_panel(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if not check_if_admin(user_id):
        bot.answer_callback_query(call.id, "❌ У вас нет прав администратора!")
        return
    
    # Создаем админ-панель
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton("📈 Изменить цены", callback_data="change_prices"),
        InlineKeyboardButton("👥 Добавить админа", callback_data="add_admin_ui"),
        InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
    )
    
    # Кнопка для просмотра списка админов
    keyboard.add(
        InlineKeyboardButton("👁️ Показать админов", callback_data="show_admins")
    )
    
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text=f"*⚙️ Админ-панель*\n\n"
             f"👤 Ваш ID: `{user_id}`\n"
             f"👥 Всего админов: {len(ADMIN_IDS)}\n\n"
             f"Выберите действие:",
        parse_mode='Markdown',
        reply_markup=keyboard
    )

# Изменение цен
@bot.callback_query_handler(func=lambda call: call.data == "change_prices")
def ask_price_change(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if not check_if_admin(user_id):
        bot.answer_callback_query(call.id, "❌ Нет прав!")
        return
    
    # Сохраняем состояние пользователя
    user_states[user_id] = 'waiting_for_percentage'
    
    # Запрашиваем процент
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_panel"))
    
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text="*📈 Изменение цен*\n\nВведите процент изменения цен:\n\n"
             "Примеры:\n"
             "• `+10.5` - увеличить на 10.5%\n"
             "• `-5` - уменьшить на 5%\n"
             "• `0` - оставить без изменений\n\n"
             "⚠️ *Внимание:* Изменение затронет все товары!",
        parse_mode='Markdown',
        reply_markup=keyboard
    )

# Обработка введенного процента
@bot.message_handler(func=lambda message: message.from_user.id in user_states and user_states[message.from_user.id] == 'waiting_for_percentage')
def process_percentage(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    try:
        # Парсим процент
        percentage_text = message.text.strip().replace('%', '').replace(',', '.')
        percentage = float(percentage_text)
        
        # Проверяем разумность значения
        if percentage < -50 or percentage > 100:
            bot.send_message(
                chat_id,
                "❌ Процент должен быть в диапазоне от -50 до +100%",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")
                )
            )
            return
        
        # Показываем уведомление о начале операции
        processing_msg = bot.send_message(
            chat_id,
            f"⏳ *Изменяю цены на {percentage:+g}%...*\n\n"
            f"Пожалуйста, подождите. Это может занять несколько секунд.",
            parse_mode='Markdown'
        )
        
        # Отправляем запрос на изменение цен
        response = update_prices_api(user_id, percentage)
        
        # Удаляем сообщение "обработка"
        bot.delete_message(chat_id, processing_msg.message_id)
        
        if response.get('success'):
            # Успешно
            if percentage >= 0:
                emoji = "📈"
                action = "увеличены"
            else:
                emoji = "📉"
                action = "уменьшены"
            
            bot.send_message(
                chat_id,
                f"{emoji} *Цены успешно изменены!*\n\n"
                f"Изменение: *{percentage:+g}%*\n"
                f"Цены {action} для всех товаров.\n"
                f"✅ {response.get('message', 'Операция выполнена')}\n\n"
                f"🔄 *Обновите мини-приложение, чтобы увидеть новые цены*",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🔙 В админ-панель", callback_data="admin_panel"),
                    InlineKeyboardButton("🏪 В магазин", web_app=WebAppInfo(
                        url="https://drochilla2281488.github.io/frontend.github.io/"
                    ))
                )
            )
        else:
            # Ошибка
            bot.send_message(
                chat_id,
                f"❌ *Ошибка:* {response.get('error', 'Неизвестная ошибка')}",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🔙 Попробовать снова", callback_data="change_prices")
                )
            )
        
        # Сбрасываем состояние
        del user_states[user_id]
        
    except ValueError:
        bot.send_message(
            chat_id,
            "❌ *Неверный формат!*\n\n"
            "Введите число. Примеры:\n"
            "• `10.5` - увеличить на 10.5%\n"
            "• `-5` - уменьшить на 5%\n"
            "• `0` - оставить без изменений",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 Назад", callback_data="change_prices")
            )
        )

# Команда для быстрого изменения цен
@bot.message_handler(commands=['changeprice'])
def changeprice_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not check_if_admin(user_id):
        bot.reply_to(message, "❌ У вас нет прав администратора!")
        return
    
    # Устанавливаем состояние
    user_states[user_id] = 'waiting_for_percentage'
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Отмена", callback_data="admin_panel"))
    
    bot.send_message(
        chat_id,
        "*📈 Изменение цен (команда)*\n\n"
        "Введите процент изменения цен:\n"
        "Пример: `+15` или `-7.5`\n\n"
        "Или нажмите 'Отмена'",
        parse_mode='Markdown',
        reply_markup=keyboard
    )

# Команда для открытия админ-панели
@bot.message_handler(commands=['admin'])
def admin_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not check_if_admin(user_id):
        bot.reply_to(message, "❌ У вас нет прав администратора!")
        return
    
    # Показываем админ-панель
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton("📈 Изменить цены", callback_data="change_prices"),
        InlineKeyboardButton("👥 Добавить админа", callback_data="add_admin"),
        InlineKeyboardButton("🏪 Магазин", web_app=WebAppInfo(
            url="https://drochilla2281488.github.io/frontend.github.io/"
        ))
    )
    
    bot.send_message(
        chat_id,
        "*⚙️ Админ-панель*\n\nВыберите действие:",
        parse_mode='Markdown',
        reply_markup=keyboard
    )

# Команда для добавления админа
@bot.message_handler(commands=['addadmin'])
def add_admin_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Проверяем, является ли отправитель админом
    if not check_if_admin(user_id):
        bot.reply_to(message, "❌ У вас нет прав для добавления админов!")
        return
    
    # Парсим команду: /addadmin 123456789
    try:
        # Разбиваем сообщение на части
        parts = message.text.split()
        
        if len(parts) != 2:
            bot.reply_to(
                message,
                "*Использование:* `/addadmin TELEGRAM_ID`\n\n"
                "*Пример:* `/addadmin 987654321`\n\n"
                "Чтобы узнать ID пользователя:\n"
                "1. Попросите его написать `/id` этому боту\n"
                "2. Или используйте @userinfobot\n"
                "3. Или попросите его нажать на кнопку ниже:",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("👤 Получить мой ID", callback_data="get_my_id")
                )
            )
            return
        
        new_admin_id = int(parts[1])
        
        # Проверяем, не пытаемся ли добавить себя
        if new_admin_id == user_id:
            bot.reply_to(message, "❌ Вы уже админ!")
            return
        
        # Проверяем, не админ ли уже этот пользователь
        if new_admin_id in ADMIN_IDS:
            bot.reply_to(message, f"❌ Пользователь `{new_admin_id}` уже админ!")
            return
        
        # Добавляем в Google Sheets через API
        logger.info(f"🔄 Добавляю админа {new_admin_id} через API...")
        response = add_admin_api(user_id, new_admin_id)
        
        if response.get('success'):
            # Добавляем в локальный список
            ADMIN_IDS.append(new_admin_id)
            
            bot.reply_to(
                message,
                f"✅ *Администратор добавлен!*\n\n"
                f"• ID: `{new_admin_id}`\n"
                f"• Добавил: `{user_id}`\n"
                f"• Время: {time.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"Локальный список обновлен. Всего админов: *{len(ADMIN_IDS)}*",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("👥 Показать всех админов", callback_data="show_admins_list")
                )
            )
            
            # Отправляем уведомление новому админу (если он писал боту)
            try:
                bot.send_message(
                    new_admin_id,
                    f"🎉 *Вам выданы права администратора!*\n\n"
                    f"Теперь у вас есть доступ к админ-панели ParfumDEPO.\n\n"
                    f"*Доступные команды:*\n"
                    f"• /admin - админ-панель\n"
                    f"• /changeprice - изменить цены\n"
                    f"• /addadmin - добавить админа\n\n"
                    f"Выдал права: `{user_id}`",
                    parse_mode='Markdown'
                )
            except:
                logger.warning(f"⚠️ Не удалось отправить уведомление новому админу {new_admin_id}")
                
        else:
            bot.reply_to(
                message,
                f"❌ *Ошибка API:* {response.get('error', 'Неизвестная ошибка')}",
                parse_mode='Markdown'
            )
            
    except ValueError:
        bot.reply_to(
            message,
            "❌ *Неверный формат ID!*\n\n"
            "ID должен быть числом. Пример: `123456789`",
            parse_mode='Markdown'
        )
    except Exception as e:
        bot.reply_to(
            message,
            f"❌ *Ошибка:* {str(e)}",
            parse_mode='Markdown'
        )

# Показать список админов
@bot.callback_query_handler(func=lambda call: call.data == "show_admins")
def show_admins_list(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if not check_if_admin(user_id):
        bot.answer_callback_query(call.id, "❌ Нет прав!")
        return
    
    # Формируем список админов
    admin_list = ""
    for i, admin_id in enumerate(ADMIN_IDS, 1):
        try:
            # Пробуем получить имя админа
            chat = bot.get_chat(admin_id)
            name = chat.first_name or f"ID: {admin_id}"
            admin_list += f"{i}. {name} (`{admin_id}`)\n"
        except:
            admin_list += f"{i}. `{admin_id}` (неизвестно)\n"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("➕ Добавить админа", callback_data="add_admin_ui"),
        InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")
    )
    
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text=f"*👥 Список администраторов*\n\n"
             f"{admin_list}\n"
             f"Всего: *{len(ADMIN_IDS)}* администраторов",
        parse_mode='Markdown',
        reply_markup=keyboard
    )

# ============================================
# API ФУНКЦИИ
# ============================================

def update_prices_api(user_id, percentage):
    """Отправляет запрос на изменение цен"""
    try:
        logger.info(f"🔄 Отправка запроса на изменение цен: {percentage}%")
        
        payload = {
            'action': 'UPDATE_PRICES',
            'user_id': user_id,
            'percentage': percentage
        }
        
        response = requests.post(
            API_URL,
            json=payload,
            timeout=60
        )
        
        logger.info(f"📥 Ответ API: {response.status_code}")
        logger.info(f"📊 Данные: {response.text}")
        
        return response.json()
        
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Таймаут запроса. Google Sheets долго отвечает.'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def add_admin_api(user_id, new_admin_id):
    """Добавляет нового админа"""
    try:
        payload = {
            'action': 'ADD_ADMIN',
            'user_id': user_id,
            'new_admin_id': new_admin_id
        }
        
        response = requests.post(
            API_URL,
            json=payload,
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {'success': False, 'error': str(e)}

# ============================================
# ДОПОЛНИТЕЛЬНЫЕ КОМАНДЫ
# ============================================

@bot.message_handler(commands=['id'])
def send_user_id(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username
    
    is_admin = check_if_admin(user_id)
    
    response_text = (
        f"👤 *Ваши данные:*\n\n"
        f"• ID: `{user_id}`\n"
        f"• Имя: {first_name}\n"
        f"• Username: @{username if username else 'отсутствует'}\n"
        f"• Админ: {'✅ ДА' if is_admin else '❌ НЕТ'}\n\n"
    )
    
    if is_admin:
        response_text += (
            f"🔐 *Админ-команды:*\n"
            f"• /admin - панель управления\n"
            f"• /changeprice - изменить цены\n"
            f"• /addadmin ID - добавить админа\n"
            f"• /id - показать этот ID\n\n"
            f"Ваш ID добавлен в локальный список админов."
        )
    else:
        response_text += (
            f"ℹ️ *Чтобы стать админом:*\n"
            f"1. Сообщите этот ID владельцу\n"
            f"2. Будет добавлен в список админов\n\n"
            f"Ваш ID: `{user_id}`"
        )
    
    bot.send_message(
        message.chat.id,
        response_text,
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['admins'])
def show_admins(message):
    user_id = message.from_user.id
    
    if not check_if_admin(user_id):
        bot.reply_to(message, "❌ Только для админов!")
        return
    
    admin_list = "\n".join([f"• `{admin_id}`" for admin_id in ADMIN_IDS])
    
    bot.reply_to(
        message,
        f"*👥 Список админов:*\n\n{admin_list}\n\n"
        f"Всего: {len(ADMIN_IDS)} администраторов",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['status'])
def bot_status(message):
    """Показывает статус бота"""
    bot.reply_to(
        message,
        f"✅ *Бот работает на Render.com!*\n\n"
        f"• 🤖 *Статус:* Активен\n"
        f"• 👥 *Админов:* {len(ADMIN_IDS)}\n"
        f"• 🌐 *Web App:* [Открыть магазин](https://drochilla2281488.github.io/frontend.github.io/)\n"
        f"• 🔧 *Версия:* 2.0.0\n\n"
        f"Бот работает стабильно! 🚀",
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

# ============================================
# ЗАПУСК БОТА В ОТДЕЛЬНОМ ПОТОКЕ
# ============================================

def run_bot():
    """Запускает Telegram бота в отдельном потоке"""
    logger.info("🤖 Запускаю Telegram бота в отдельном потоке...")
    
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        logger.error(f"❌ Ошибка в работе бота: {e}")
    finally:
        logger.info("🤖 Бот остановлен")

# ============================================
# ОБРАБОТКА СИГНАЛОВ
# ============================================

def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    global bot_running
    logger.info(f"📞 Получен сигнал {signum}. Останавливаю бота...")
    bot_running = False
    bot.stop_polling()
    sys.exit(0)

# ============================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ============================================

if __name__ == "__main__":
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("="*60)
    logger.info("🚀 ЗАПУСК PARFUMDEPO TELEGRAM BOT")
    logger.info("="*60)
    logger.info(f"🤖 Бот: @{bot.get_me().username}")
    logger.info(f"👥 Админов: {len(ADMIN_IDS)}")
    logger.info(f"🌐 Web App: https://drochilla2281488.github.io/frontend.github.io/")
    logger.info(f"🏠 Health Check: http://0.0.0.0:{os.environ.get('PORT', 10000)}/health")
    logger.info("="*60)
    
    # Запускаем бота в отдельном потоке
    bot_thread = Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask приложение (блокирующий вызов)
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Запуск Flask сервера на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
