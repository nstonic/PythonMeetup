from contextlib import suppress

from django.conf import settings
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, TelegramError

from tg_bot.models import Speech


def answer_to_user(
        update,
        context,
        text,
        keyboard: list[list[InlineKeyboardButton]] = None,
        add_back_button=True,
        parse_mode=None,
        edit_current_message=True
):
    """
    Функция для ответа пользователю. Рекомендуется все сообщения отправлять через нее
    :param update: Update
    :param context: Context
    :param text: Текст сообщения
    :param keyboard: Список кнопок Inline клавиатуры
    :param add_back_button: Если True, то к клавиатуре автоматически добавится кнопка "Назад" с callback_data="back"
    :param parse_mode: Режим разметки текста сообщения Markdown, HTML или None
    :param edit_current_message: Метод отправки сообщения. Если True, то новое сообщение отправляется как
    редактирование старого. Если False, то старое удаляется и присылается новое
    """
    if not keyboard:
        keyboard = []

    if add_back_button:
        keyboard.append(
            [InlineKeyboardButton('< Назад', callback_data='back')]
        )
    if edit_current_message:
        try:
            message = context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=update.effective_message.message_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=parse_mode
            )
        except TelegramError:
            pass
        else:
            return message

    with suppress(TelegramError):
        context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=update.effective_message.message_id
        )
    return context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=parse_mode
    )


def show_start_menu(update, context):
    context.user_data['current_event'] = None
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
    text = '\n'.join(speech_list) or 'Еще не заявлено ни одного докладчика'
    answer_to_user(
        update,
        context,
        text=text
    )
    return 'HANDLE_SPEECH_LIST_MENU'


def register(update, context, event_id):
    pass


def ask(update, context):
    event_id = context.user_data['current_event']
    speech = Speech.objects.get(pk=1)  # TODO получаем текущее выступление
    speaker = speech.speaker
    text = f'Задайте свой вопрос.\nТекущий спикер - <b>{speaker.fullname}</b>'
    context.user_data['speaker_id'] = speaker.id
    message = answer_to_user(
        update,
        context,
        text,
        parse_mode='HTML'
    )
    context.user_data['msg_to_delete'] = message.message_id
    return 'HANDLE_QUESTION'


def send_question(update, context, question):
    context.bot.send_message(
        chat_id=context.user_data.pop('speaker_id'),
        text=question
    )
    return show_event(update, context, context.user_data['current_event'])


def meet(update, context):
    pass


def donate(update, context, event_id):
    pass


def show_future_events(update, context):
    events = []  # TODO получаем список грядущих мероприятий
    keyboard = []
    if events:
        text = 'Вот какие мероприятия пройдут в скором времени'
        keyboard.extend([
            [InlineKeyboardButton(event.title, callback_data=event.pk)]
            for event in events
        ])
    else:
        text = 'К сожалению в ближайшее время мероприятий не ожидается'

    answer_to_user(
        update,
        context,
        text=text,
        keyboard=keyboard
    )
    return 'HANDLE_FUTURE_EVENTS'


def ask_for_event_title(update, context):
    text = 'Пришлите названия для Вашего мероприятия'
    message = answer_to_user(
        update,
        context,
        text
    )
    context.user_data['msg_to_delete'] = message.message_id
    return 'HANDLE_EVENT_TITLE'


def ask_for_event_text(update, context):
    text = 'Пришлите описание Вашего мероприятия'
    message = answer_to_user(
        update,
        context,
        text
    )
    context.user_data['msg_to_delete'] = message.message_id
    return 'HANDLE_EVENT_TEXT'


def delete_event(update, context, event_id):
    # TODO Удаляем мероприятие
    context.bot.answerCallbackQuery(
        update.callback_query.id,
        'Мероприятие удалено'
    )
    return show_start_menu(update, context)


def edit_event(update, context, title=None, text=None):
    if title:
        if event_id := context.user_data.get('current_event'):
            pass  # TODO Меняем название мероприятия
        else:
            event_id: int  # TODO Создаём в базе мероприятие. Пока только с названием. Без других данных
            context.user_data['current_event'] = event_id

    if text:
        event_id = context.user_data['current_event']
        # TODO Меняем описание мероприятия

    keyboard = [
        [InlineKeyboardButton('Изменить название', callback_data='title')],
        [InlineKeyboardButton('Изменить описание', callback_data='text')],
        [InlineKeyboardButton('Удалить', callback_data='delete')]
    ]
    text = '<b>Название мероприятия</b>\n\n' \
           'Здесь вы можете изменить название и описание мероприятия. ' \
           f'Для более подробного редактирования используйте <a href="{settings.EVENTS_URL}">админ панель</a>'

    if msg_to_delete := context.user_data.pop('msg_to_delete'):
        context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=msg_to_delete
        )
    answer_to_user(
        update,
        context,
        text,
        keyboard,
        parse_mode='HTML'
    )
    return 'HANDLE_EDIT_EVENT'
