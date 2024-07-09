from telegram import ReplyKeyboardMarkup, KeyboardButton

def get_start_menu():
    keyboard = [
        [KeyboardButton('/add_channel')],
        [KeyboardButton('/help')],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_help_menu():
    keyboard = [
        [KeyboardButton('/add_channel')],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def start(update, context):
    reply_markup = get_start_menu()
    update.message.reply_text('Привет! Я бот для отслеживания и сохранения постов из указанных каналов Telegram.', reply_markup=reply_markup)

def help(update, context):
    reply_markup = get_help_menu()
    update.message.reply_text('Доступные команды:\n'
                              '/add_channel <имя_канала> - добавить новый канал для отслеживания\n'
                              '/help - получить справку по командам бота', reply_markup=reply_markup)
