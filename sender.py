import foodgetter

def send_daily(context):
    try:
        chat_id = context.job.context
        context.bot.send_message(chat_id, text=foodgetter.get_day_message())
    except Exception as err:
        print("Daily error:")
        print(err)

def send_weekly(context):
    try:
        chat_id = context.job.context
        context.bot.send_message(chat_id, text=foodgetter.get_week_message())
    except Exception as err:
        print("Weekly error:")
        print(err)