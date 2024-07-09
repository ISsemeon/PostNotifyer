import os
from datetime import datetime
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
import logging
from dotenv import load_dotenv
import sqlite3
from threading import Lock
import json

from content_handler import *
from menu import *

# Load environment variables
load_dotenv()

# Telegram Bot token from environment variable
TOKEN = os.getenv('BOT_TOKEN')

# Check if bot token is set
if TOKEN is None:
    raise ValueError('Telegram Bot token not found in environment variables.')

# Logging configuration
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize SQLite connection and cursor in a thread-safe manner
def get_sqlite_connection():
    conn = sqlite3.connect('channels_auth.db', check_same_thread=False)
    cursor = conn.cursor()
    return conn, cursor

# Function to create channels_auth_info table if it does not exist
def create_table():
    conn, cursor = get_sqlite_connection()
    with conn:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels_auth_info (
                user_id INTEGER,
                channel TEXT,
                auth_info TEXT,
                PRIMARY KEY (user_id, channel),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

# Call function to create table if it does not exist
create_table()

# Global lock for SQLite operations
sqlite_lock = Lock()

# Function to get authentication info for a channel
def get_channel_auth_info(user_id, channel):
    conn, cursor = get_sqlite_connection()
    with conn:
        cursor.execute('SELECT auth_info FROM channels_auth_info WHERE user_id = ? AND channel = ?', (user_id, channel))
        result = cursor.fetchone()
        auth_info = json.loads(result[0]) if result and result[0] else {}
    conn.close()
    return auth_info

# Function to save authentication info for a channel
def save_channel_auth_info(user_id, channel, auth_info):
    conn, cursor = get_sqlite_connection()
    with sqlite_lock:
        with conn:
            auth_info_json = json.dumps(auth_info)
            cursor.execute('REPLACE INTO channels_auth_info (user_id, channel, auth_info) VALUES (?, ?, ?)', (user_id, channel, auth_info_json))
    conn.close()

# Function to delete authentication info for a channel
def delete_channel_auth_info(user_id, channel):
    conn, cursor = get_sqlite_connection()
    with sqlite_lock:
        with conn:
            cursor.execute('DELETE FROM channels_auth_info WHERE user_id = ? AND channel = ?', (user_id, channel))
    conn.close()

# Function to check if a channel is being tracked by a user
def is_channel_tracked(user_id, channel):
    conn, cursor = get_sqlite_connection()
    with conn:
        cursor.execute('SELECT 1 FROM channels_auth_info WHERE user_id = ? AND channel = ?', (user_id, channel))
        result = cursor.fetchone()
        return result is not None

# Функция для определения фотографии с наибольшим разрешением
def get_largest_photo(photos):
    if not photos:
        return None
    
    largest_photo = max(photos, key=lambda photo: photo.width * photo.height)
    return largest_photo

def new_posts(update, context):
    try:
        if update.channel_post and update.channel_post.chat and update.channel_post.date:
            channel_username = update.channel_post.chat.username
            user_id = update.effective_user.id

            if user_id is None or channel_username is None:
                logging.warning('Skipping processing due to missing user ID or channel username.')
                return

            if not is_channel_tracked(user_id, channel_username):
                logging.info(f'Update not related to tracked channels for user: {channel_username}')
                return

            auth_info = get_channel_auth_info(user_id, channel_username)

            # Continue with processing as before
            post_timestamp = update.channel_post.date.timestamp()
            post_datetime = datetime.utcfromtimestamp(post_timestamp)
            post_date = post_datetime.strftime('%Y-%m-%d_%H-%M-%S')
            post_folder = os.path.join('./posts', f'post_{post_date}')
            os.makedirs(post_folder, exist_ok=True)

            caption = update.channel_post.caption
            save_post_text(caption, post_folder)

            largest_photo = get_largest_photo(update.channel_post.photo)
            if largest_photo:
                save_photo(largest_photo, post_folder, context)

            if update.channel_post.video:
                save_video(update.channel_post.video, post_folder, context)

            if update.channel_post.document:
                save_document(update.channel_post.document, post_folder, context)

            if update.channel_post.audio:
                save_audio(update.channel_post.audio, post_folder, context)

        else:
            logging.warning('Update does not contain required attributes (channel_post, chat, date).')

    except Exception as e:
        logging.error(f'Error processing post: {e}')

# Function to add a new channel for tracking
def add_channel(update, context):
    try:
        user_id = update.effective_user.id
        new_channel = context.args[0]
        auth_info = context.args[1] if len(context.args) > 1 else {}

        if not is_channel_tracked(user_id, new_channel):
            save_channel_auth_info(user_id, new_channel, auth_info)
            logging.info(f'Added new channel for tracking: {new_channel} (user: {user_id})')
            update.message.reply_text(f'Channel {new_channel} added for tracking.')
        else:
            update.message.reply_text(f'Channel {new_channel} is already being tracked.')

    except IndexError:
        update.message.reply_text('Please provide channel name and auth_info.')

    except Exception as e:
        logging.error(f'Error adding channel: {e}')
        update.message.reply_text('Failed to add channel. Please try again later.')

# Function to list user's tracked channels
def my_channels(update, context):
    try:
        user_id = update.effective_user.id
        channels = []

        conn, cursor = get_sqlite_connection()
        with conn:
            cursor.execute('SELECT channel FROM channels_auth_info WHERE user_id = ?', (user_id,))
            result = cursor.fetchall()
            channels = [row[0] for row in result]
        conn.close()

        if channels:
            update.message.reply_text(f'You are tracking the following channels: {", ".join(channels)}')
        else:
            update.message.reply_text('You are not tracking any channels yet.')

    except Exception as e:
        logging.error(f'Error listing channels: {e}')
        update.message.reply_text('Failed to list channels. Please try again later.')

# Start command handler
def start(update, context):
    reply_markup = get_start_menu()
    update.message.reply_text('Hello! I am a bot to track and save posts from Telegram channels.', reply_markup=reply_markup)

# Error handler
def error(update, context):
    logging.warning(f'Update {update} caused error {context.error}')

# Main function to start the bot
def main():
    try:
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher

        # Add handlers for different commands and message types
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("add_channel", add_channel, pass_args=True))
        dp.add_handler(CommandHandler("my_channels", my_channels))
        dp.add_handler(MessageHandler(Filters.update.channel_posts, new_posts))
        dp.add_error_handler(error)

        # Start the bot
        updater.start_polling()
        logging.info('Bot started. Listening for new posts...')
        updater.idle()

    except Exception as e:
        logging.error(f'Error in main function: {e}')

if __name__ == '__main__':
    main()
