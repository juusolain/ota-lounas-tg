from sender import send_weekly
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.utils import helpers
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, PicklePersistence, Defaults

import timepicker
import utils
import foodgetter

from datetime import time

WEBHOOK_BASE_URL = 'https://ota-lounas-tg-webhook.jusola.xyz'

log_chat_id = '@ota_lounas_dev'

def get_channel_chat_id() -> str:
    modef = open('mode', 'r')
    mode = modef.read().strip()
    modef.close()
    if mode == 'dev':
        chat_id = '@ota_lounas_dev'
    elif mode == 'prod':
        chat_id = '@otalounas'
    return chat_id

def get_token() -> str:
    """Get bot token from file"""
    tf = open('token', 'r')
    token = tf.read().strip()
    tf.close()
    return token

def handle_info(update: Update, context: CallbackContext) -> None:
    utils.send_info(update, context)
    update.message.delete()

def handle_start(update: Update, context: CallbackContext) -> None:
    """Start setup on /start"""
    answer_options = [
        [InlineKeyboardButton("Joka päivä", callback_data={"action": "set_frequency", "daily": True, "weekly": False}),
        InlineKeyboardButton("Viikon alussa", callback_data={"action": "set_frequency", "weekly": True, "daily": False})],
        [InlineKeyboardButton("Molempina", callback_data={"action": "set_frequency", "daily": True, "weekly": True})],
        [InlineKeyboardButton("En milloinkaan", callback_data={"action": "clear_frequency"})]
    ]
    # Reply with questions
    reply_markup = InlineKeyboardMarkup(answer_options, one_time_keyboard=True)

    update.message.reply_text('Milloin haluat ruokalistan?',reply_markup=reply_markup)
     
    # Delete command message
    update.message.delete()

def handle_send_today(update: Update, context: CallbackContext) -> None:
    try:
        update.message.reply_text(foodgetter.get_day_message())
    except Exception as err:
        print(err)
        utils.send_autodelete(update, context, "Vaikuttaisi siltä, että tänään ei ole ruokaa\n Onko tämä virheellistä: @juusolain", 60)
    update.message.delete()

def handle_send_week(update: Update, context: CallbackContext) -> None:
    try:
        update.message.reply_text(foodgetter.get_week_message())
    except Exception as err:
        print(err)
        utils.send_autodelete(update, context, "Vaikuttaisi siltä, että tällä viikolla ei ole ruokaa\n Onko tämä virheellistä: @juusolain", 60)
    update.message.delete()

def handle_button(update: Update, context: CallbackContext) -> None:
    """Handle button press"""
    query = update.callback_query
    query.answer()

    # Get data
    data = query.data
    action = data['action']

    # Set timer(s)
    if action == "set_frequency":
        # Set weekly and daily settings
        context.user_data['daily'] = data['daily']
        context.user_data['weekly'] = data['weekly']

        # Remove old jobs
        id = query.message.chat.id
        remove_job(f'weekly-{id}', context)
        remove_job(f'daily-{id}', context)
        
        # Ask time
        timepicker.start(update, context)
        # Delete setup msg
        query.delete_message()
    elif action == "clear_frequency":
        # Remove jobs
        id = query.message.chat.id
        remove_job(f'weekly-{id}', context)
        remove_job(f'daily-{id}', context)

        # Empty userdata
        context.user_data.clear()
        # Reply
        utils.send_autodelete(update, context, 'Selvä, et \(enää\) saa ruokalistoja', 15)
        # Delete setup msg
        query.delete_message()
        
    elif action == "timepicker":
        timepicker.handler(update, context)
    else:
        update.message.reply_text('Jokin meni vikaan... kokeile uudestaan lähettämällä /start')
        query.delete_message()

def remove_job(name: str, context: CallbackContext) -> None:
    jobs = context.job_queue.get_jobs_by_name(name)
    for job in jobs:
        job.schedule_removal()

def send_channel(context) -> None:
    try:
        context.bot.send_message(get_channel_chat_id(), text=foodgetter.get_day_message())
    except Exception as err:
        context.bot.send_message(log_chat_id, text="Error while sending foods")
        context.bot.send_message(log_chat_id, text=helpers.escape_markdown(str(err), 2))

def bot_main() -> None:
    """Start bot"""

    defaults = Defaults(parse_mode=ParseMode.MARKDOWN_V2)
    # Create persistence for buttons to work after bot restart
    persistence = PicklePersistence(
        'bot.pickle', store_callback_data=True, store_user_data=True, store_bot_data=True
    )

    # Create updater
    token = get_token()
    updater = Updater(token, persistence=persistence, arbitrary_callback_data=True, defaults=defaults)

    dispatcher = updater.dispatcher

    # Restore send jobs
    print("Restoring send jobs")
    for uid, data in dispatcher.user_data.items():
        try:
            utils.set_jobs(uid, data, dispatcher.job_queue)
        except Exception as err:
            print("Err while setting jobs", str(err))

    print("Send jobs restored")

    print("Adding normal jobs")

    dispatcher.job_queue.run_daily(send_channel, time(7,0,0), days=(0,1,2,3,4), name='channel')
    dispatcher.job_queue.run_daily(foodgetter.load_foods, time(0,0,1), days=(0,1,2,3,4), name='foodloader')

    # Add handlers
    dispatcher.add_handler(CommandHandler('start', handle_start))
    dispatcher.add_handler(CommandHandler('info', handle_info))
    dispatcher.add_handler(CommandHandler('viikko', handle_send_week))
    dispatcher.add_handler(CommandHandler('ruoka', handle_send_today))
    dispatcher.add_handler(CallbackQueryHandler(handle_button))

    # Start webhook
    updater.start_webhook(listen='0.0.0.0', port=8443, url_path=token, webhook_url=f"{WEBHOOK_BASE_URL}/{token}")

    print("Bot up")

    updater.idle()