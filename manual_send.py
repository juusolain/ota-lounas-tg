from telegram import Update
from telegram.ext import Updater
import datetime
lunchdata = None

tf = open('token', 'r')
token = tf.read().strip()
tf.close()
#dev -1001468852318, prod: -1001219068606

chat_id = 0

modef = open('mode', 'r')
mode = modef.read().strip()
modef.close()
if mode == 'dev':
    chat_id = -1001468852318
elif mode == 'prod':
    chat_id = -1001219068606

def bot_start():
    updater = Updater(token)
    return updater

def format_message(foods, humandate):
    ret = "*"
    ret += humandate.replace('.', '\.')
    ret += "*\n"
    for food in foods:
        ret += "\- "
        ret += food.replace('.', '\.').replace('-', '\-')
        ret += "\n"
    return ret

updater = bot_start()
foods = []
humandate = input("Input human date: ")
foodcount = int(input("Amount of foods today: "))
for i in range(foodcount):
    foods.append(input("Input food: "))
if foods == None or humandate == None:
    print("Couldn't send message")
else:
    message = format_message(foods, humandate)
    date_now = datetime.date.today()
    if date_now.isoweekday() < 6:
        updater.bot.send_message(chat_id=chat_id, text=message, parse_mode='MarkdownV2')

updater.stop()
