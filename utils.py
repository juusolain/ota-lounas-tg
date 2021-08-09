from datetime import time
import sender


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
    return f'{hour:02d}:{minute:02d}'

def delmsg(context):
    msg = context.job.context
    msg.delete()

def send_info(update, context, isnew=False):
    frequency_text = get_frequency_text(context.user_data['weekly'], context.user_data['daily'])
    time_text = get_time_text(context.user_data["time_hour"],context.user_data["time_minute"])

    message = update.message or update.callback_query.message

    if isnew:
        nyt = "nyt "
    else:
        nyt = ""

    # Send reply
    reply = message.reply_text(f'Saat {nyt}ruokalistan {frequency_text} klo {time_text}')
        # Schedule reply deletion
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
    t = time(user_data['time_hour'], user_data['time_hour'])

    # Queue jobs
    if user_data['daily']:
        job_queue.run_daily(sender.send_daily, t, context=id, days=(0,1,2,3,4), name=f'daily-{id}')
    if user_data['weekly']:
        job_queue.run_daily(sender.send_weekly, t, context=id, days=(0,), name=f'weekly-{id}')