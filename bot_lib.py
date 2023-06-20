from telegram import InlineKeyboardMarkup, InlineKeyboardButton


def show_start_menu(update, context):
    user_id = update.effective_chat.id
    event_id = 1  # TODO Ищем мероприятие которое сейчас проходит, если нет, то ближайшее, которое ожидается
    text = 'Добро пожаловать в бот PythonMeetup'
    keyboard = [
        [InlineKeyboardButton('Ближайшее мероприятие', callback_data=event_id)],
        [InlineKeyboardButton('Расписание мероприятий', callback_data='future_events')]
    ]
    if user_id:  # TODO Сюда вставить проверку является ли пользователь админом
        keyboard.append(
            [InlineKeyboardButton('Создать мероприятие', callback_data='create_event')]
        )

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return 'HANDLE_MAIN_MENU'


def show_event(update, context, event_id):
    context.user_data['current_event'] = event_id

    event = None  # TODO получаем данные о мероприятии
    event_title = 'Учим python-telegram-bot'
    event_text = 'Сильно учим'

    user_id = update.effective_chat.id
    user = None  # TODO получаем данные о пользователе

    keyboard = [
        [InlineKeyboardButton('Расписание выступлений', callback_data='speech_list')],
        [InlineKeyboardButton('Назад', callback_data='main_menu')]
    ]
    if not user:  # TODO Проверяем, что пользователь не зарегистрирован как участник данного мероприятия
        keyboard.insert(
            1,
            [InlineKeyboardButton('Регистрация', callback_data='register')]
        )
    else:
        if True:  # TODO Проверяем, что мероприятие проходит в данный момент
            keyboard.insert(
                1,
                [InlineKeyboardButton('Задать вопрос', callback_data='ask'),
                 InlineKeyboardButton('Познакомиться', callback_data='meet')]
            )

    if user:  # TODO Проверяем, является ли пользователь организатором данного мероприятия
        keyboard.insert(
            2,
            [InlineKeyboardButton('Редактировать', callback_data='edit')]
        )
    else:
        keyboard.insert(
            2,
            [InlineKeyboardButton('Задонатить', callback_data='donate')]
        )

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'<b>{event_title}</b>\n\n{event_text}',
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return 'HANDLE_EVENT_MENU'


def show_speech_list(update, context, event_id):
    pass


def register(update, context, event_id):
    pass


def ask(update, context):
    pass


def meet(update, context):
    pass


def edit(update, context, event_id):
    pass


def donate(update, context, event_id):
    pass


def show_future_events(update, context):
    pass


def create_event(update, context):
    pass
