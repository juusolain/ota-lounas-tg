from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

import utils

def start(update, context) -> None:
    """Start timepicker"""
    # Init times if dont exist yet
    init_userdata_time(context)
    # Reply with KB for entering time
    reply_markup = InlineKeyboardMarkup(get_kb(context.user_data['time_hour'], context.user_data['time_minute']))
    update.callback_query.message.reply_text('Entä moneltako haluat ruokalistan?', reply_markup=reply_markup)

def init_userdata_time(context) -> None:
    """Set initial time values"""
    if not 'time_hour' in context.user_data:
        context.user_data['time_hour'] = 7
    if not 'time_minute' in context.user_data:
        context.user_data['time_minute'] = 0

def get_kb(hour, minute) -> None:
    """Create KB rows"""
    return [
        [
            InlineKeyboardButton("+", callback_data={"action": "timepicker", "timepicker_action": "inc", "timepicker_target": "hour"}),
            InlineKeyboardButton("+", callback_data={"action": "timepicker", "timepicker_action": "inc", "timepicker_target": "min"}),
        ],
        [
            InlineKeyboardButton(f"{hour:02d}", callback_data={"action": "timepicker", "timepicker_action": None}),
            InlineKeyboardButton(f"{minute:02d}", callback_data={"action": "timepicker", "timepicker_action": None}),
        ],
        [
            InlineKeyboardButton("-", callback_data={"action": "timepicker", "timepicker_action": "dec", "timepicker_target": "hour"}),
            InlineKeyboardButton("-", callback_data={"action": "timepicker", "timepicker_action": "dec", "timepicker_target": "min"}),
        ],
        [
            InlineKeyboardButton("OK", callback_data={"action": "timepicker", "timepicker_action": "ok"}),
        ]
    ]


def handler(update: Update, context: CallbackContext) -> None:
    """Handle button reply"""
    query = update.callback_query
    data = query.data

    if data['timepicker_action'] == 'ok':
        # Set jobs
        chat_id = update.callback_query.message.chat.id
        utils.set_jobs(chat_id, context.user_data, context.job_queue)
        # Get frequency and time text for reply
        utils.send_info(update, context, isnew=True)
        # Delete old time query
        query.delete_message()
        return

    if not 'timepicker_target' in data:
        return

    # Handle minutes
    if data["timepicker_target"] == 'min':
        # Get offset based on increase or decrease
        offset = 1
        if data["timepicker_action"] == 'inc':
            pass
        elif data["timepicker_action"] == 'dec':
            offset = -offset
        else:
            offset = 0

        # Add offset
        context.user_data['time_minute'] += offset

        # Handle rollovers
        while (context.user_data['time_minute'] > 59):
            context.user_data['time_minute'] -= 60
            context.user_data['time_hour'] += 1

        while (context.user_data['time_minute'] < 0):
            context.user_data['time_minute'] += 60
            context.user_data['time_hour'] -= 1

    # Handle hours
    if data["timepicker_target"] == 'hour':
        # Get offset based on increase or decrease
        offset = 1
        if data["timepicker_action"] == 'inc':
            pass
        elif data["timepicker_action"] == 'dec':
            offset = -offset
        else:
            offset = 0
        # Add offset
        context.user_data['time_hour'] += offset
    
    # Deal with hour rollovers (can also be caused by minutes)
    while (context.user_data['time_hour'] > 23):
        context.user_data['time_hour'] -= 24

    while (context.user_data['time_hour'] < 0):
        context.user_data['time_hour'] += 24

    # Update KB
    reply_markup = InlineKeyboardMarkup(get_kb(context.user_data['time_hour'], context.user_data['time_minute']))
    query.edit_message_reply_markup(reply_markup=reply_markup)

