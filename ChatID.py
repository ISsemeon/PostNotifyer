import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Вставьте сюда токен вашего бота
TELEGRAM_BOT_TOKEN = 'TELEGRAM_BOT_TOKEN'

# Установка уровня логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    update.message.reply_text(f'Chat ID этой группы: {chat_id}')
    logger.info(f'Chat ID группы: {chat_id}')

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
