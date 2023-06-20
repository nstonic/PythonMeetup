from contextlib import suppress

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, TelegramError


def answer_to_user(
        update,
        context,
        text,
        keyboard=None,
        add_back_button=True,
        parse_mode=None,
        delete_current_message=True
):
    """
    Функция для ответа пользователю. Рекомендуется все сообщения отправлять через нее
    :param update: Update
    :param context: Context
    :param text: Текст сообщения
    :param keyboard: Список кнопок Inline клавиатуры
    :param add_back_button: Если True, то к клавиатуре автоматически добавится кнопка "Назад" с callback_data="back"
    :param parse_mode: Режим разметки текста сообщения Markdown, HTML или None
    :param delete_current_message: Если True, то перед отправкой нового сообщения удалится старое
    """

    if add_back_button:
        keyboard.append(
            [InlineKeyboardButton('Назад', callback_data='back')]
        )
    if delete_current_message:
        with suppress(TelegramError):
            context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=update.effective_message.message_id
            )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=parse_mode
    )


def show_start_menu(update, context):
    user_id = update.effective_chat.id
    event_id = 1  # TODO Ищем мероприятие, которое сейчас проходит. Если нет, то ближайшее, которое ожидается
    text = 'Добро пожаловать в бот PythonMeetup'
    keyboard = [
        [InlineKeyboardButton('Ближайшее мероприятие', callback_data=event_id)],
        [InlineKeyboardButton('Расписание мероприятий', callback_data='future_events')]
    ]
    if user_id:  # TODO Сюда вставить проверку является ли пользователь админом
        keyboard.append(
            [InlineKeyboardButton('Создать мероприятие', callback_data='create_event')]
        )

    answer_to_user(
        update,
        context,
        text=text,
        keyboard=keyboard,
        add_back_button=False
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
        [InlineKeyboardButton('Расписание выступлений', callback_data='speech_list')]
    ]
    if not user:  # TODO Проверяем, что пользователь не зарегистрирован как участник данного мероприятия
        keyboard.append(
            [InlineKeyboardButton('Регистрация', callback_data='register')]
        )
    else:
        if True:  # TODO Проверяем, что мероприятие проходит в данный момент
            keyboard.append(
                [InlineKeyboardButton('Задать вопрос', callback_data='ask'),
                 InlineKeyboardButton('Познакомиться', callback_data='meet')]
            )

    if user:  # TODO Проверяем, является ли пользователь организатором данного мероприятия
        keyboard.append(
            [InlineKeyboardButton('Редактировать', callback_data='edit')]
        )
    else:
        keyboard.append(
            [InlineKeyboardButton('Задонатить', callback_data='donate')]
        )

    answer_to_user(
        update,
        context,
        text=f'<b>{event_title}</b>\n\n{event_text}',
        keyboard=keyboard,
        parse_mode='HTML'
    )
    return 'HANDLE_EVENT_MENU'


def show_speech_list(update, context, event_id):
    speech_list = []  # TODO получаем данные о выступлениях на данном мероприятии
    answer_to_user(
        update,
        context,
        text='\n'.join(speech_list)
    )
    return 'HANDLE_SPEECH_LIST_MENU'


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
    events = []  # TODO получаем список грядущих мероприятий
    keyboard = None
    if events:
        text = 'Вот какие мероприятия пройдут в скором времени'
        keyboard = [
            [InlineKeyboardButton(event.title, callback_data=event.pk)]
            for event in events
        ]
    else:
        text = 'К сожалению в ближайшее время мероприятий не ожидается'

    answer_to_user(
        update,
        context,
        text=text,
        keyboard=keyboard
    )
    return 'HANDLE_FUTURE_EVENTS'


def create_event(update, context):
    pass
