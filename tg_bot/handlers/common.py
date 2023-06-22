from contextlib import suppress

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, TelegramError
from telegram.ext import CallbackContext

from tg_bot.models import Event, User, Speech
from datetime import datetime


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


def get_closest_event_to_dt(qs, dt):
    event = qs.objects.filter(started_at__gte=dt, finished_at__lte=dt).first()
    if not event:
        event = qs.objects.filter(started_at__gte=dt).order_by("started_at").first()
    return event


def show_start_menu(update, context):
    user_id = update.effective_chat.id
    event_id = get_closest_event_to_dt(Event, datetime.now()).id  # TODO Ищем мероприятие, которое сейчас проходит. Если нет, то ближайшее, которое ожидается
    text = 'Добро пожаловать в бот PythonMeetup'
    context.user_data['current_event'] = event_id
    keyboard = [
        [InlineKeyboardButton('Ближайшее мероприятие', callback_data=event_id)],
        [InlineKeyboardButton('Расписание мероприятий', callback_data='future_events')]
    ]
    user = User.objects.get(telegram_id=user_id)
    if user.is_admin:  # TODO Сюда вставить проверку является ли пользователь админом
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

    event = Event.objects.get(id=event_id)  # TODO получаем данные о мероприятии
    event_title = event.title
    event_text = event.description

    user_id = update.effective_chat.id
    user = User.objects.get(telegram_id=user_id)  # TODO получаем данные о пользователе

    keyboard = [
        [InlineKeyboardButton('Расписание выступлений', callback_data='speech_list')]
    ]
    if user not in event.members.all():  # TODO Проверяем, что пользователь не зарегистрирован как участник данного мероприятия
        keyboard.append(
            [InlineKeyboardButton('Регистрация', callback_data='register')]
        )
    else:
        if event.started_at <= datetime.now():  # TODO Проверяем, что мероприятие проходит в данный момент
            keyboard.append(
                [InlineKeyboardButton('Задать вопрос', callback_data='ask'),
                 InlineKeyboardButton('Познакомиться', callback_data='meet')]
            )

    if user in event.organizers.all():  # TODO Проверяем, является ли пользователь организатором данного мероприятия
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
    speech_list = Speech.objects.filter(event=event_id)  # TODO получаем данные о выступлениях на данном мероприятии
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
    pass


def meet(update, context):
    pass


def donate(update, context, event_id):
    pass


def show_future_events(update, context):
    events = Event.objects.filter(started_at__gte=datetime.now()) # TODO получаем список грядущих мероприятий
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


def delete_event(update, context: CallbackContext, event_id):
    # TODO Удаляем мероприятие
    Event.objects.filter(event=event_id).delete()
    context.bot.answerCallbackQuery(
        update.callback_query.id,
        'Мероприятие удалено'
    )
    return show_start_menu(update, context)


def edit_event(update, context, title=None, text=None):
    if title:
        if event_id := context.user_data.get('current_event'):
            Event.objects.filter(event=event_id).update(title=update.message.text)  # TODO Меняем название мероприятия
        else:
            Event.objects.create(title=update.message.text, organizers=update.message.text)  # TODO Создаём в базе мероприятие. Пока только с названием. Без других данных
            context.user_data['current_event'] = event_id

    if text:
        event_id = context.user_data['current_event']
        Event.objects.filter(event=event_id).update(description=update.message.text)
        # TODO Меняем описание мероприятия

    keyboard = [
        [InlineKeyboardButton('Изменить название', callback_data='title')],
        [InlineKeyboardButton('Изменить описание', callback_data='text')],
        [InlineKeyboardButton('Удалить', callback_data='delete')]
    ]
    text = '<b>Название мероприятия</b>\n\n' \
           'Здесь вы можете изменить название и описание мероприятия. ' \
           'Для более подробного редактирования используйте <a href="127.0.0.1:8000">админ панель</a>'  # TODO ссылка на админку

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
