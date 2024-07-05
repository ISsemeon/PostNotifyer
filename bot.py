import os
from datetime import datetime
from telegram.ext import Updater, MessageHandler, Filters
import logging

# Укажите свой токен бота здесь
TOKEN = 'TELEGRAM_BOT_TOKEN'

# Укажите имя вашего канала без символа @
CHANNEL_USERNAME = 'botTesterss'

# Папка для сохранения постов
POSTS_FOLDER = './posts'

# Создаем папку для постов, если её еще нет
os.makedirs(POSTS_FOLDER, exist_ok=True)

# Настройка логгирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Функция для определения наибольшего разрешения фотографии
def get_largest_photos(photos):
    largest_photos = []
    largest_size = 0

    for photo in photos:
        photo_size = photo.width * photo.height
        if photo_size > largest_size:
            largest_size = photo_size
            largest_photos = [photo]
        elif photo_size == largest_size:
            largest_photos.append(photo)

    return largest_photos

# Функция для обработки новых постов
def new_posts(update, context):
    try:
        # Проверяем, что обновление связано с вашим каналом
        if update.channel_post and update.channel_post.chat.username == CHANNEL_USERNAME:
            # Получаем дату и время поста в виде временной метки (timestamp)
            post_timestamp = update.channel_post.date.timestamp()

            # Преобразуем временную метку в объект datetime для форматирования
            post_datetime = datetime.utcfromtimestamp(post_timestamp)

            # Форматируем дату и время поста
            post_date = post_datetime.strftime('%Y-%m-%d_%H-%M-%S')

            # Создаем отдельную папку для текущего поста с датой и временем
            post_folder = os.path.join(POSTS_FOLDER, f'post_{post_date}')
            os.makedirs(post_folder, exist_ok=True)

            # Сохраняем текст поста в текстовый файл, если он есть
            if update.channel_post.text:
                text_file_path = os.path.join(post_folder, 'text.txt')
                with open(text_file_path, 'w', encoding='utf-8') as text_file:
                    text_file.write(update.channel_post.text)
                logging.info(f'Сохранен текст поста в файл: {text_file_path}')
            else:
                logging.info('В посте отсутствует текст')

            # Получаем список фотографий в посте
            photos = update.channel_post.photo

            if photos:
                # Выбираем фотографии с наибольшим разрешением
                largest_photos = get_largest_photos(photos)
                for idx, photo in enumerate(largest_photos):
                    # Получаем информацию о файле фотографии
                    file_id = photo.file_id
                    file = context.bot.get_file(file_id)
                    # Скачиваем фотографию в папку текущего поста
                    photo_file_path = os.path.join(post_folder, f'photo_{idx}.jpg')
                    file.download(photo_file_path)
                    logging.info(f'Сохранена фотография: {photo_file_path}')
            else:
                logging.info('В посте отсутствуют фотографии')
    except Exception as e:
        # Логируем ошибку
        logging.error(f'Ошибка при обработке поста: {e}')

# Настройка и запуск бота
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Обрабатываем только новые посты из вашего канала
    dp.add_handler(MessageHandler(Filters.update.channel_posts, new_posts))

    # Запускаем бота и начинаем проверку обновлений
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
