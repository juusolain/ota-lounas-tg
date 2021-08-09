import foodgetter

def send_daily(context):
    try:
        id = context.job.context
        context.bot.send_message(id, text=foodgetter.get_day_message())
    except Exception as err:
        print(err)

def send_weekly(context):
    try:
        id = context.job.context
        context.bot.send_message(id, text=foodgetter.get_week_message())
    except Exception as err:
        print(err)