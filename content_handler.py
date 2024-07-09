import os
import logging

# Папка для сохранения постов
POSTS_FOLDER = './posts'

# Создаем папку для постов, если её еще нет
os.makedirs(POSTS_FOLDER, exist_ok=True)

# Функция для сохранения текста поста
def save_post_text(caption, post_folder):
    try:
        if caption:
            text_file_path = os.path.join(post_folder, 'caption.txt')
            with open(text_file_path, 'w', encoding='utf-8') as text_file:
                text_file.write(caption)
            logging.info(f'Сохранен caption поста в файл: {text_file_path}')
        else:
            logging.info('В посте отсутствует caption')
    except Exception as e:
        logging.error(f'Ошибка при сохранении caption поста: {e}')

# Функция для сохранения фотографии
def save_photo(photo, post_folder, context):
    try:
        # Получаем информацию о файле фотографии
        file_id = photo.file_id
        file = context.bot.get_file(file_id)

        # Получаем оригинальное имя файла
        file_name = file.file_path.split('/')[-1]

        # Скачиваем фотографию в папку текущего поста с оригинальным именем
        photo_file_path = os.path.join(post_folder, file_name)
        file.download(photo_file_path)
        logging.info(f'Сохранена фотография: {photo_file_path}')
    except Exception as e:
        logging.error(f'Ошибка при сохранении фотографии: {e}')
