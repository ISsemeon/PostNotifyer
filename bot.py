import os
from datetime import datetime
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
import logging
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, KeyboardButton
from content_handler import save_post_text, save_photo, POSTS_FOLDER  # Импортируем функции и переменную из content_handler
from menu import start, help  # Импортируем функции из menu.py

# Загружаем переменные окружения из файла .env, если он есть
load_dotenv()

# Получаем токен бота из переменной окружения
TOKEN = os.getenv('BOT_TOKEN')

# Проверяем, что токен был установлен
if TOKEN is None:
    raise ValueError('Не удалось найти токен бота в переменных окружения.')

# Настройка логгирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Список каналов для отслеживания
CHANNEL_USERNAMES = ['botTesterss']

# Глобальная переменная для диспетчера
dp = None

# Функция для определения фотографии с наибольшим разрешением
def get_largest_photo(photos):
    if not photos:
        return None
    
    largest_photo = max(photos, key=lambda photo: photo.width * photo.height)
    return largest_photo

# Функция для обработки новых постов
def new_posts(update, context):
    try:
        # Проверяем, что обновление связано с вашими каналами и что есть channel_post
        if update.channel_post and hasattr(update.channel_post, 'chat') and hasattr(update.channel_post, 'date'):
            channel_username = update.channel_post.chat.username
            if channel_username in CHANNEL_USERNAMES:
                # Получаем дату и время поста в виде временной метки (timestamp)
                post_timestamp = update.channel_post.date.timestamp()

                # Преобразуем временную метку в объект datetime для форматирования
                post_datetime = datetime.utcfromtimestamp(post_timestamp)

                # Форматируем дату и время поста
                post_date = post_datetime.strftime('%Y-%m-%d_%H-%M-%S')

                # Создаем отдельную папку для текущего поста с датой и временем
                post_folder = os.path.join(POSTS_FOLDER, f'post_{post_date}')
                os.makedirs(post_folder, exist_ok=True)

                caption = update.channel_post.caption
                save_post_text(caption, post_folder)

                # Получаем фотографию с наибольшим разрешением
                largest_photo = get_largest_photo(update.channel_post.photo)
                
                # Сохраняем фотографию
                if largest_photo:
                    save_photo(largest_photo, post_folder, context)
            else:
                logging.info(f'Обновление не связано с вашими каналами или отсутствует необходимая информация: {channel_username}')
    except Exception as e:
        logging.error(f'Ошибка при обработке поста: {e}')

def add_channel(update, context):
    # Создаем список кнопок для добавления канала
    keyboard = [
        [KeyboardButton('/start')],
        [KeyboardButton('/help')],
    ]

    # Создаем клавиатуру из списка кнопок
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    new_channel = context.args[0]
    if new_channel not in CHANNEL_USERNAMES:
        CHANNEL_USERNAMES.append(new_channel)
        logging.info(f'Добавлен новый канал для отслеживания: {new_channel}')
        update.message.reply_text(f'Канал {new_channel} добавлен для отслеживания.', reply_markup=reply_markup)
        dp.add_handler(MessageHandler(Filters.update.channel_posts, new_posts))
    else:
        update.message.reply_text(f'Канал {new_channel} уже отслеживается.', reply_markup=reply_markup)

# Настройка и запуск бота
def main():
    global dp  # Объявляем dp как глобальную переменную
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Обрабатываем только новые посты из указанных каналов
    dp.add_handler(MessageHandler(Filters.update.channel_posts, new_posts))
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help))

    # Команда для добавления нового канала для отслеживания
    dp.add_handler(CommandHandler('add_channel', add_channel, pass_args=True))

    # Запускаем бота и начинаем проверку обновлений
    updater.start_polling()
    logging.info('Бот запущен. Ожидание новых постов...')
    updater.idle()

if __name__ == '__main__':
    main()
