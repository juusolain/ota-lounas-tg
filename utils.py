from datetime import time
import sender

from tzlocal import get_localzone


def get_frequency_text(weekly, daily):
    if weekly and daily:
        return 'joka päivä ja viikon alussa'
    elif weekly:
        return 'viikon alussa'
    elif daily:
        return 'joka päivä'
    else:
        return 'et milloinkaan'

def get_time_text(hour, minute):
    try:
        return f'klo {hour:02d}:{minute:02d}'
    except TypeError as err:
        return ''
    except Exception as err:
        print("Time text error", str(err))
        return None

def delmsg(context):
    msg = context.job.context
    msg.delete()

def send_info(update, context, isnew=False):
    frequency_text = get_frequency_text(context.user_data.get('weekly'), context.user_data.get('daily'))
    time_text = get_time_text(context.user_data.get("time_hour"),context.user_data.get("time_minute"))

    message = update.message or update.callback_query.message

    if isnew:
        nyt = "nyt "
    else:
        nyt = ""

    # Send reply
    reply = message.reply_text(f'Saat {nyt}ruokalistan {frequency_text} {time_text}')
        # Schedule reply deletion
    if not isnew:
        context.job_queue.run_once(delmsg, 15, context=reply)

def send_autodelete(update, context, text, time):
    message = update.message or update.callback_query.message

    # Send reply
    reply = message.reply_text(text)
    # Schedule reply deletion
    context.job_queue.run_once(delmsg, time, context=reply)

def set_jobs(chat_id, user_data, job_queue) -> None:
    """Create jobs"""
    # Get time
    t = time(user_data.get('time_hour'), user_data.get('time_minute'),0,tzinfo=get_localzone())

    # Queue jobs
    if user_data.get('daily'):
        job_queue.run_daily(sender.send_daily, t, context=chat_id, days=(0,1,2,3,4), name=f'daily-{chat_id}')
    if user_data.get('weekly'):
        job_queue.run_daily(sender.send_weekly, t, context=chat_id, days=(0,), name=f'weekly-{chat_id}')