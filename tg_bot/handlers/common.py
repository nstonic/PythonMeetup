import json
import os
from contextlib import suppress
from datetime import timedelta

from django.conf import settings
from django.utils.datetime_safe import datetime
from django.utils.timezone import now
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, TelegramError, Update
from telegram.ext import CallbackContext

from tg_bot.models import Event, User, Speech


def answer_to_user(
        update: Update,
        context: CallbackContext,
        text,
        keyboard: list[list[InlineKeyboardButton]] = None,
        image=None,
        add_back_button=True,
        parse_mode=None
):
    """
    Функция для ответа пользователю. Рекомендуется все сообщения отправлять через нее
    :param update: Update
    :param context: Context
    :param text: Текст сообщения
    :param keyboard: Список кнопок Inline клавиатуры
    :param image: Ссылка на фото
    :param add_back_button: Если True, то к клавиатуре автоматически добавится кнопка "Назад" с callback_data="back"
    :param parse_mode: Режим разметки текста сообщения Markdown, HTML или None
    """

    if not keyboard:
        keyboard = []
    if add_back_button:
        keyboard.append(
            [InlineKeyboardButton('< Назад', callback_data='back')]
        )

    if not image:
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

    if image:
        media_root = os.path.join(settings.BASE_DIR, 'media')
        with open(os.path.join(media_root, image.strip(r'\/')), 'rb') as photo:
            message = context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=photo.read(),
                caption=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=parse_mode
            )
    else:
        message = context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=parse_mode
        )
    with suppress(TelegramError):
        context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=update.effective_message.message_id
        )
    return message


def show_start_menu(update: Update, context):
    user_id = update.effective_chat.id
    context.user_data['current_event'] = None
    keyboard = [
        [InlineKeyboardButton('Расписание мероприятий', callback_data='future_events')]
    ]

    event = Event.objects.get_current_or_closest()
    if event:
        button_text = f'Сейчас проходит {event.title}' if event.started_at < now() else f'Скоро {event.title}'
        keyboard.insert(
            0,
            [InlineKeyboardButton(button_text, callback_data=event.id)]
        )

    user, created = User.objects.get_or_create(
        telegram_id=user_id,
        defaults={
            'nickname': update.effective_chat.username or user_id,
            'fullname': update.effective_chat.full_name or user_id
        }
    )
    if user.is_admin:
        keyboard.append(
            [InlineKeyboardButton('Создать мероприятие', callback_data='create_event')]
        )

    text = 'Добро пожаловать в бот PythonMeetup'
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

    event = Event.objects.get(id=int(event_id))
    event_title = event.title
    event_text = event.description

    user_id = update.effective_chat.id
    user = User.objects.get(telegram_id=user_id)

    keyboard = [
        [InlineKeyboardButton('Расписание выступлений', callback_data='speech_list')]
    ]

    if event.started_at <= now():
        keyboard.append(
            [InlineKeyboardButton('Задать вопрос', callback_data='ask'),
             InlineKeyboardButton('Познакомиться', callback_data='meet')]
        )

    if user in event.organizers.all():
        keyboard.append(
            [InlineKeyboardButton('Редактировать', callback_data='edit')]
        )
    else:
        keyboard.append(
            [InlineKeyboardButton('Задонатить', callback_data='donate')]
        )

    text = f'<b>{event_title}</b>'
    if event.started_at < now():
        text += f'\n<b>Проходит прямо сейчас</b>.\nЗакончится {event.finished_at.strftime("%d.%m.%Y %H:%M")}.'
    else:
        text += f'\nПроходит с {event.started_at.strftime("%d.%m.%Y %H:%M")} по {event.finished_at.strftime("%d.%m.%Y %H:%M")}.'
    text += f'\n\n{event_text}'

    answer_to_user(
        update,
        context,
        text=text,
        image=event.image.url if event.image else None,
        keyboard=keyboard,
        parse_mode='HTML'
    )
    return 'HANDLE_EVENT_MENU'


def show_speech_list(update, context, event_id):
    speeches = Speech.objects.filter(event=event_id).order_by('-started_at')
    speech_list = [
        f'<b>{speech.started_at.strftime("%H:%M")}-{speech.finished_at.strftime("%H:%M")}</b> {speech.title}'
        for speech in speeches
    ]
    text = '\n'.join(speech_list) or 'Еще не заявлено ни одного докладчика'
    answer_to_user(
        update,
        context,
        text=text,
        parse_mode='HTML'
    )
    return 'HANDLE_SPEECH_LIST_MENU'


def ask(update, context):
    speech = Speech.objects.get_current()
    if speech:
        speaker = speech.speaker
        text = f'Задайте свой вопрос.\nТекущий спикер - <b>{speaker.fullname}</b>'
        context.user_data['speaker_id'] = speaker.id
    else:
        text = f'Дождитесь начала выступления'
    message = answer_to_user(
        update,
        context,
        text,
        parse_mode='HTML'
    )
    context.user_data['msg_to_delete'] = message.message_id
    return 'HANDLE_QUESTION'


def send_question(update, context, question):
    try:
        user = User.objects.get(update.effective_chat.id)
        text = f'Вопрос от слушателя {user.fullname}:\n\n{question}'
        context.bot.send_message(
            chat_id=context.user_data.pop('speaker_id'),
            text=text
        )
    finally:
        return show_event(update, context, context.user_data['current_event'])


def meet(update, context):
    user_id = update.effective_chat.id
    name = update.effective_chat.username
    member, _ = User.objects.get_or_create(telegram_id=user_id, nickname=name)
    if not member.fullname:
        answer_to_user(
            update,
            context,
            text='Введите, пожалуйста, свое полное имя'
        )
        return 'HANDLE_FULLNAME'
    else:
        return ask_age(update, context)


def donate(update, context, event_id):
    pass


def show_future_events(update, context):
    context.user_data['current_event'] = None
    events = Event.objects.filter_futures()
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
        text,
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


def ask_age(update, context):
    text = 'Сколько Вам лет? (введите цифрами)'
    answer_to_user(
        update,
        context,
        text,
        add_back_button=False,
        edit_current_message=False,
    )
    return 'HANDLE_AGE'


def ask_activity(update, context):
    text = 'Укажите, пожалуйста, Ваш род деятельности'
    answer_to_user(
        update,
        context,
        text,
        add_back_button=False,
    )
    return 'HANDLE_ACTIVITY'


def ask_stack(update, context):
    text = 'Опишите свои навыки, применяемый стек технологий'
    answer_to_user(
        update,
        context,
        text,
        add_back_button=False,
    )
    return 'HANDLE_STACK'


def ask_hobby(update, context):
    text = 'Есть ли у Вас хобби? Какое?'
    answer_to_user(
        update,
        context,
        text,
        add_back_button=False,
    )
    return 'HANDLE_HOBBY'


def ask_purpose(update, context):
    text = 'Опишите, пожалуйста, какие цели Вы ожидаете достичь в ходе встречи'
    answer_to_user(
        update,
        context,
        text,
        add_back_button=False,
    )
    return 'HANDLE_PURPOSE'


def delete_event(update, context, event_id):
    Event.objects.filter(pk=event_id).delete()
    context.bot.answer_callback_query(
        update.callback_query.id,
        'Мероприятие удалено'
    )
    return show_start_menu(update, context)


def edit_event(update, context, title=None, text=None):
    if title:
        if event_id := context.user_data.get('current_event'):
            Event.objects.filter(pk=int(event_id)).update(title=update.message.text)
        else:
            event = Event.objects.create(title=update.message.text)
            event.organizers.set(User.objects.filter(telegram_id=update.message.from_user.id))
            event_id = event.id
            context.user_data['current_event'] = event_id
    elif text:
        event_id = context.user_data['current_event']
        Event.objects.filter(pk=int(event_id)).update(description=update.message.text)

    event = Event.objects.get(pk=int(context.user_data['current_event']))

    keyboard = [
        [InlineKeyboardButton('Изменить название', callback_data='title')],
        [InlineKeyboardButton('Изменить описание', callback_data='text')],
        [InlineKeyboardButton('Удалить мероприятие', callback_data='delete')]
    ]
    text = f'<b>{event.title}</b>\n\n' \
           'Здесь вы можете изменить название и описание мероприятия. ' \
           f'Для более подробного редактирования используйте ' \
           f'<a href="{settings.EVENTS_URL.rstrip("/")}/tg_bot/event/{event.id}/change/">админ панель</a>'

    if msg_to_delete := context.user_data.get('msg_to_delete'):
        with suppress(TelegramError):
            context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=msg_to_delete
            )
        context.user_data['msg_to_delete'] = None
    answer_to_user(
        update,
        context,
        text,
        keyboard,
        parse_mode='HTML'
    )
    return 'HANDLE_EDIT_EVENT'


def save_member(update, context, **attrs):
    current_user = User.objects.get(telegram_id=update.effective_chat.id)
    for attr, value in attrs.items():
        if attr == 'meeters':
            event_id = context.user_data['current_event']
            event = Event.objects.get(pk=event_id)
            event.meeters.add(current_user)
            event.save()
            continue
        setattr(current_user, attr, value)
    current_user.save()
    return


def extend_speech(update, context):
    json_raw = update.callback_query.data.replace('extend_', '', 1)
    extending_data = json.loads(json_raw)
    moment = datetime.fromtimestamp(extending_data.get('ts', now().timestamp()))
    extending_time = extending_data.get('extend', 0)
    speech = Speech.objects.get_current(moment=moment)
    if not speech.finished_at < now():
        speech.finished_at += timedelta(minutes=extending_time)
        if extending_time == 0:
            speech.do_not_notify = True
        else:
            speech.do_not_notify = False
            with suppress(TelegramError):
                context.bot.answer_callback_query(
                    update.callback_query.id,
                    f'Выступление продлено на {extending_time} минут'
                )
        speech.save()

    with suppress(TelegramError):
        context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=update.effective_message.message_id
        )
