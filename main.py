from sender import send_weekly
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.utils import helpers
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, PicklePersistence, Defaults

from tzlocal import get_localzone
import datetime

import threading
import timepicker
import utils
import foodgetter
import json

WEBHOOK_BASE_URL = 'https://ota-lounas-tg-webhook.jusola.xyz'

log_chat_id = '@ota_lounas_dev'

def get_mode() -> str:
    modef = open('mode', 'r')
    mode = modef.read().strip()
    modef.close()
    return mode

def get_channel_chat_id() -> str:
    mode = get_mode()
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

def get_admins() -> list:
    """Get admins from file"""
    af = open('admins', 'r')
    admins = af.read().strip().split()
    af.close()
    return admins

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
        utils.send_autodelete(update, context, "Vaikuttaisi siltä, että tänään ei ole ruokaa\nJos olen väärässä, laita viestiä: @juusolain", 60)
    update.message.delete()

def handle_send_week(update: Update, context: CallbackContext) -> None:
    try:
        update.message.reply_text(foodgetter.get_week_message())
    except Exception as err:
        print(err)
        utils.send_autodelete(update, context, "Vaikuttaisi siltä, että tällä viikolla ei ole ruokaa\nJos olen väärässä, laita viestiä: @juusolain", 60)
    update.message.delete()

# Admin
def handle_manual_channel_send_week(update: Update, context: CallbackContext) -> None:
    try:
        if not str(update.message.from_user.id) in get_admins():
            print(f"Manual send from nonadmin {update.message.from_user.id} - ignoring")
            return
        context.bot_data['weekly_sent'] = send_channel_weekly(context)
        print("Sent manual weekly")
    except Exception as err:
        print(err)
        utils.send_autodelete(update, context, err, 60)
    update.message.delete()

# Admin
def handle_manual_channel_send_daily(update: Update, context: CallbackContext) -> None:
    try:
        if not str(update.message.from_user.id) in get_admins():
            print(f"Manual send from nonadmin {update.message.from_user.id} - ignoring")
            return
        send_channel_daily(context)
        print("Sent manual daily")
    except Exception as err:
        print(err)
        utils.send_autodelete(update, context, err, 60)
    update.message.delete()

def handle_set_foods(update: Update, context: CallbackContext) -> None:
    try:
        if not str(update.message.from_user.id) in get_admins():
            print(f"Manual setfoods from nonadmin {update.message.from_user.id} - ignoring")
            return
        parts = update.message.text.split(" ", 2)
        if not len(parts) == 3:
            utils.send_autodelete(update, context, 'Invalid format, use /setfoods nextweek foodsJson\nnextweek = [this, next]. This = this weeks foods, next for next weeks\nfoodsJson is the foods JSON stringified')
        if not parts[1] in ['this', 'next']:
            utils.send_autodelete(update, context, 'Invalid nextweek value. Use this for this week or next for next week')
        isNextWeek = (parts[1] == 'next')
        new_foods = json.loads(parts[2])

        foodgetter.manual_set_foods(new_foods, isNextWeek=isNextWeek)

        print("Set foods manually")
    except Exception as err:
        print(err)
        utils.send_autodelete(update, context, err, 60)
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
        chat_id = query.message.chat.id
        remove_job(f'weekly-{chat_id}', context)
        remove_job(f'daily-{chat_id}', context)
        
        # Ask time
        timepicker.start(update, context)
        # Delete setup msg
        query.delete_message()
    elif action == "clear_frequency":
        # Remove jobs
        chat_id = query.message.chat.id
        remove_job(f'weekly-{chat_id}', context)
        remove_job(f'daily-{chat_id}', context)

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

def send_channel_daily(context) -> bool:
    try:
        context.bot.send_message(get_channel_chat_id(), text=foodgetter.get_day_message())
        return True
    except Exception as err:
        context.bot.send_message(log_chat_id, text="Error while sending foods")
        context.bot.send_message(log_chat_id, text=helpers.escape_markdown(str(err), 2))
        return False

def send_channel_weekly_monday(context) -> None:
    if not context.bot_data['weekly_sent']:
        send_channel_weekly(context)

def send_channel_weekly_sunday(context) -> None:
    context.bot_data['weekly_sent'] = send_channel_weekly(context, isNextWeek=True)

def send_channel_weekly(context, isNextWeek=False) -> bool:
    try:
        context.bot.send_message(get_channel_chat_id(), text=foodgetter.get_week_message(isNextWeek=isNextWeek))
        return True
    except Exception as err:
        context.bot.send_message(log_chat_id, text="Error while sending foods")
        context.bot.send_message(log_chat_id, text=helpers.escape_markdown(str(err), 2))
        return False

def start_load_foods(*argv) -> None:
    wd = datetime.date.today().weekday()
    isNextWeek = (wd == 6)
    print("Starting food load thread")
    t = threading.Thread(target=foodgetter.load_foods, args=[isNextWeek])
    t.start()

def main() -> None:
    """Start bot"""
    defaults = Defaults(parse_mode=ParseMode.MARKDOWN_V2, tzinfo=get_localzone())
    # Create persistence for buttons to work after bot restart
    persistence = PicklePersistence(
        'bot.pickle', store_callback_data=True, store_user_data=True, store_bot_data=True
    )

    # Create updater
    token = get_token()
    updater = Updater(token, persistence=persistence, arbitrary_callback_data=True, defaults=defaults)

    dispatcher = updater.dispatcher

    # Load foods
    start_load_foods()

    # Restore send jobs
    print("Restoring send jobs")
    for uid, data in dispatcher.user_data.items():
        try:
            if uid and data:
                utils.set_jobs(uid, data, dispatcher.job_queue)
            else:
                print("Not setting jobs, uid or data null")
        except Exception as err:
            print("Err while setting jobs", str(err))

    print("Send jobs restored")

    print("Adding normal jobs")

    dispatcher.job_queue.run_daily(send_channel_daily, datetime.time(7,0,0,tzinfo=get_localzone()), days=(0,1,2,3,4), name='channel-daily') # send daily
    dispatcher.job_queue.run_daily(send_channel_weekly_sunday, datetime.time(18,0,0,tzinfo=get_localzone()), days=(6,), name='channel-weekly-sunday') # send weekly on sunday if available
    dispatcher.job_queue.run_daily(send_channel_weekly_monday, datetime.time(6,59,59,tzinfo=get_localzone()), days=(0,), name='channel-weekly-monday') # send weekly on monday if sunday didn't work

    dispatcher.job_queue.run_daily(start_load_foods, datetime.time(0,0,1,tzinfo=get_localzone()), days=(0,1,2,3,4), name='foodloader-daily') # load foods at midnight
    dispatcher.job_queue.run_daily(start_load_foods, datetime.time(17,50,0,tzinfo=get_localzone()), days=(6,), name='foodloader-nextweek') # load foods just before sunday-weekly for max chance of having food

    # Add handlers
    dispatcher.add_handler(CommandHandler('start', handle_start))
    dispatcher.add_handler(CommandHandler('info', handle_info))
    dispatcher.add_handler(CommandHandler('channel_weekly', handle_manual_channel_send_week))
    dispatcher.add_handler(CommandHandler('channel_daily', handle_manual_channel_send_daily))
    dispatcher.add_handler(CommandHandler('viikko', handle_send_week))
    dispatcher.add_handler(CommandHandler('ruoka', handle_send_today))
    dispatcher.add_handler(CommandHandler('set_foods', handle_set_foods))
    dispatcher.add_handler(CallbackQueryHandler(handle_button))

    updater.start_polling()

    print("Bot up")

    updater.idle()

if __name__ == '__main__':
    main()
