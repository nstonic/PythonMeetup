from environs import Env
from telegram.ext import (
    Updater,
    CallbackQueryHandler,
    MessageHandler,
    CommandHandler,
    Filters
)

from bot_lib import show_events, show_start_menu


def handle_main_menu(update, context):
    query = update.callback_query.data
    if query == 'events':
        return show_events(update, context)


def handle_users_reply(update, context):

    if update.message:
        user_reply = update.message.text
    elif update.callback_query:
        user_reply = update.callback_query.data
    else:
        return

    if user_reply in ['/start', 'start']:
        user_state = 'START'
    else:
        user_state = context.user_data.get('state')

    state_functions = {
        'START': show_start_menu
    }

    state_handler = state_functions.get(user_state, show_start_menu)
    next_state = state_handler(
        update=update,
        context=context
    ) or user_state
    context.user_data['state'] = next_state


def main():
    env = Env()
    env.read_env()
    token = env('TG_TOKEN')
    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    updater.start_polling()


if __name__ == '__main__':
    main()
