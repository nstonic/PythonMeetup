import json
import time

import telegram
from django.conf import settings
from django.core.management import BaseCommand
from django.utils.timezone import now
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from tg_bot.models import Speech


class Command(BaseCommand):

    def handle(self, *args, **options):
        while True:
            if current_speech := Speech.objects.get_current():
                if current_speech.do_not_notify:
                    continue
                time_left = current_speech.finished_at - now()
                if time_left.seconds < 300:
                    self.send_notification(current_speech)
            time.sleep(10)

    @staticmethod
    def send_notification(speech):
        token = settings.TG_TOKEN
        bot = telegram.Bot(token=token)
        text = f'Выступление текущего докладчика - {speech.speaker.fullname} - подходит к концу.\n' \
               f'Если ему нужно еще время, можете продлить его выступление, выбрав один из вариантов ниже'
        callback_data = {
            'speech': speech.id,
            'ts': int(now().timestamp())
        }
        extends = {
            '+5 мин': 5,
            '+10 мин': 10,
            '+15 мин': 15,
            'Не продлевать': 0
        }
        buttons = []
        for button_text, extending_time in extends.items():
            callback_data['extend'] = extending_time
            json_raw = json.dumps(callback_data)
            buttons.append(InlineKeyboardButton(button_text, callback_data=f'extend_{json_raw}'))

        keyboard = InlineKeyboardMarkup([
            buttons[:-1],
            [buttons[-1]]
        ])
        organizers = speech.event.organizers.all()
        for organizer in organizers:
            bot.send_message(
                chat_id=organizer.telegram_id,
                text=text,
                reply_markup=keyboard
            )
        speech.do_not_notify = True
        speech.save()
