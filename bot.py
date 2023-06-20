from functools import partial

from environs import Env
from telegram.ext import (
    Updater,
    CallbackQueryHandler,
    MessageHandler,
    CommandHandler,
    Filters
)

from bot_lib import (
    show_future_events,
    show_start_menu,
    create_event,
    show_event,
    show_speech_list,
    register,
    ask,
    meet,
    edit,
    donate
)


def handle_main_menu(update, context):
    query = update.callback_query.data
    actions = {
        'future_events': show_future_events,
        'create_event': create_event
    }
    action = actions.get(
        query,
        partial(show_event, event_id=query)
    )
    print(action)
    action(update, context)


def handle_event_menu(update, context):
    query = update.callback_query.data
    event_id = context.user_data['current_event']
    actions = {
        'speech_list': partial(show_speech_list, event_id=event_id),
        'main_menu': show_start_menu,
        'register': partial(register, event_id=event_id),
        'ask': ask,
        'meet': meet,
        'edit': partial(edit, event_id=event_id),
        'donate': partial(donate, event_id=event_id)
    }
    action = actions.get(query)
    action(update, context)


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
        'START': show_start_menu,
        'HANDLE_MAIN_MENU': handle_main_menu,
        'HANDLE_EVENT_MENU': handle_event_menu
    }

    state_handler = state_functions.get(user_state, show_start_menu)

    next_state = state_handler(
        update=update,
        context=context
    )

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
