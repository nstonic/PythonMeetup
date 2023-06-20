from telegram import InlineKeyboardMarkup, InlineKeyboardButton


def show_start_menu(update, context):
    text = 'Основное меню'
    keyboard = [
        [InlineKeyboardButton('Расписание мероприятий', callback_data='events')],
    ]
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return 'HANDLE_MAIN_MENU'


def show_events(update, context):
    pass
