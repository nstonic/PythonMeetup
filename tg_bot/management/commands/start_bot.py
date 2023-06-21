from django.core.management import BaseCommand
from environs import Env
from telegram.ext import (
    Updater,
    CallbackQueryHandler,
    MessageHandler,
    CommandHandler,
    Filters
)

from tg_bot.handlers.menu_handlers import handle_users_reply


class Command(BaseCommand):

    def handle(self, *args, **options):
        env = Env()
        env.read_env()
        token = env('TG_TOKEN')
        updater = Updater(token)
        dispatcher = updater.dispatcher
        dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
        dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
        dispatcher.add_handler(CommandHandler('start', handle_users_reply))
        updater.start_polling()


if __name__ == '__main__':  # Для упрощенного запуска в IDE
    Command().handle()
