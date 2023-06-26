import json
import random
import os
from contextlib import suppress
from datetime import timedelta

from django.conf import settings
from django.utils.datetime_safe import datetime
from django.utils.timezone import now

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, TelegramError, Update, LabeledPrice
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
            [InlineKeyboardButton('🔙 Назад', callback_data='back')]
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
        with open(os.path.join(settings.BASE_DIR, image.strip(r'\/')), 'rb') as photo:
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
    context.user_data['out'] = []
    keyboard = [
        [InlineKeyboardButton('📅 Расписание мероприятий', callback_data='future_events')]
    ]

    event = Event.objects.get_current_or_closest()
    if event:
        button_text = f'🔥 Сейчас проходит {event.title}' if event.started_at < now() else f'🔜 Скоро {event.title}'
        keyboard.insert(
            0,
            [InlineKeyboardButton(button_text, callback_data=event.id)]
        )

    user, created = User.objects.get_or_create(
        telegram_id=user_id,
        defaults={
            'nickname': update.effective_chat.username or user_id,
        }
    )
    if user.is_admin:
        keyboard.append(
            [InlineKeyboardButton('🆕 Создать мероприятие', callback_data='create_event')]
        )

    text = '<b>Добро пожаловать в PythonMeetup</b>\n' \
           'Я помогу вам быть в курсе конференций, посвященных теме Python разработки. ' \
           'А так же задать вопрос выступающему и найти полезные знакомства в ходе самого мероприятия.'
    answer_to_user(
        update,
        context,
        text=text,
        keyboard=keyboard,
        image='logo.png',
        add_back_button=False,
        parse_mode='HTML'
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
        [InlineKeyboardButton('📋 Расписание выступлений', callback_data='speech_list')]
    ]

    if event.started_at and event.started_at <= now():
        keyboard.append(
            [InlineKeyboardButton('❔ Вопрос выступающему', callback_data='ask'),
             InlineKeyboardButton('🙋 Познакомиться', callback_data='meet')]
        )

    if user in event.organizers.all():
        keyboard.append(
            [InlineKeyboardButton('⚙ Редактировать', callback_data='edit')]
        )
    else:
        keyboard.append(
            [InlineKeyboardButton('💳 Задонатить', callback_data='donate')]
        )

    text = f'<b>{event_title}</b>'
    if not event.started_at:
        text += '\n<b>Сроки прохождения еще не известны</b>'
    elif event.started_at < now():
        text += f'\n<b>Проходит прямо сейчас</b>.\n' \
                f'Закончится {event.finished_at.strftime("%d.%m.%Y")}.'
    else:
        text += f'\nБудет проходить с {event.started_at.strftime("%d.%m.%Y")}' \
                f' по {event.finished_at.strftime("%d.%m.%Y")}.'
    text += f'\n\n{event_text}'

    answer_to_user(
        update,
        context,
        text=text,
        image=f'media/{event.image.url}' if event.image else None,
        keyboard=keyboard,
        parse_mode='HTML'
    )
    return 'HANDLE_EVENT_MENU'


def show_speech_list(update, context, event_id):
    speeches = Speech.objects.filter(event=event_id).order_by('started_at')
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
        context.user_data['speaker_id'] = speaker.telegram_id
    else:
        text = 'Дождитесь начала выступления'
    message = answer_to_user(
        update,
        context,
        text,
        parse_mode='HTML'
    )
    context.user_data['msg_to_delete'] = message.message_id
    return 'HANDLE_QUESTION'


def send_question(update, context, question):
    user = User.objects.get(telegram_id=update.effective_chat.id)
    text = f'Вопрос от слушателя {user.fullname}:\n\n{question}'
    context.bot.send_message(
        chat_id=context.user_data.pop('speaker_id'),
        text=text
    )
    return show_event(update, context, context.user_data['current_event'])


def meet(update, context):
    user_id = update.effective_chat.id
    name = update.effective_chat.username
    member, _ = User.objects.get_or_create(telegram_id=user_id, nickname=name)
    event = Event.objects.get(pk=context.user_data['current_event'])
    members = event.meeters.exclude(telegram_id__in=context.user_data['out'])
    out_count = len(context.user_data['out']) + 1
    if member in members:
        if event.meeters.count() - out_count:
            meeter = random.choice(members.exclude(telegram_id=user_id))
            context.user_data['out'].append(meeter.telegram_id)
            text = f'Познакомьтесь с участником {meeter.fullname}.\nРод деятельности: {meeter.activity}\nПришел с целью: {meeter.purpose}'
            keyboard = []
            keyboard.append(
                [InlineKeyboardButton('👍 Хочу поговорить', callback_data=meeter.telegram_id),
                 InlineKeyboardButton('💩 Показать другого', callback_data='next')]
            )
            answer_to_user(
                update,
                context,
                text,
                add_back_button=False,
                keyboard=keyboard,
            )
        else:
            text = 'В настоящее время нет других желающих пообщаться.'
            answer_to_user(
                update,
                context,
                text,
            )
        return 'HANDLE_MEETING'
    elif not member.fullname:
        answer_to_user(
            update,
            context,
            text='Введите, пожалуйста, свое полное имя',
            add_back_button=False,
        )
        return 'HANDLE_FULLNAME'
    else:
        return ask_age(update, context)


def donate(update, context):
    chat_id = update.message.chat_id
    title = "Донат"
    description = "Donate using python-telegram-bot"
    payload = "Custom-Payload"
    provider_token = settings.PAYMENT_TOKEN
    currency = "RUB"
    price = 10
    prices = [LabeledPrice("Донат", price * 100)]

    context.bot.send_invoice(
        chat_id, title, description, payload, provider_token, currency, prices
    )


def precheckout_callback(update, context):
    query = update.pre_checkout_query
    if query.invoice_payload != 'Custom-Payload':
        query.answer(ok=False, error_message="Что то пошло не так...")
    else:
        query.answer(ok=True)


def successful_payment_callback(update, context):
    update.message.reply_text("Спасибо за ваше пожертовавание!")
    return show_start_menu(update, context)

  
def show_meeter(update, context: CallbackContext, meeter_id):
    meeter = User.objects.get(telegram_id=meeter_id)
    nickname = meeter.nickname
    text = f'Вы можете связаться с {meeter.fullname} по ссылке https://t.me/{nickname}'
    answer_to_user(
            update,
            context,
            text,
            add_back_button=True,
            )
    return 'HANDLE_MEETING'


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
        [InlineKeyboardButton('📝 Изменить название', callback_data='title')],
        [InlineKeyboardButton('📝 Изменить описание', callback_data='text')],
        [InlineKeyboardButton('❌ Удалить мероприятие', callback_data='delete')]
    ]
    text = f'<b>{event.title}</b>'
    if not event.started_at:
        text += '\n<b>Сроки проведения еще не известны</b>'
    elif event.started_at < now():
        text += f'\n<b>Проходит прямо сейчас</b>.\n' \
                f'Закончится {event.finished_at.strftime("%d.%m.%Y")}.'
    else:
        text += f'\nПроходит с {event.started_at.strftime("%d.%m.%Y")}' \
                f' по {event.finished_at.strftime("%d.%m.%Y")}.'
    if event.description:
        text += f'\n\n{event.description[:80]} ...'
    text += '\n\n-----------\n' \
            'Здесь вы можете изменить название и описание мероприятия. ' \
            'Для более подробного редактирования используйте ' \
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
        parse_mode='HTML',
        image=f'media/{event.image.url}' if event.image else None
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
