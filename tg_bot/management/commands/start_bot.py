from django.conf import settings
from django.core.management import BaseCommand
from telegram.ext import (
    Updater,
    CallbackQueryHandler,
    MessageHandler,
    CommandHandler,
    Filters,
    PreCheckoutQueryHandler
)

from tg_bot.handlers.menu_handlers import handle_users_reply
from tg_bot.handlers.common import precheckout_callback, successful_payment_callback


class Command(BaseCommand):

    def handle(self, *args, **options):
        token = settings.TG_TOKEN
        updater = Updater(token)
        dispatcher = updater.dispatcher
        dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
        dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
        dispatcher.add_handler(CommandHandler('start', handle_users_reply))
        dispatcher.add_handler(PreCheckoutQueryHandler(precheckout_callback))
        dispatcher.add_handler(MessageHandler(Filters.successful_payment, successful_payment_callback))
        updater.start_polling()
        updater.idle()
