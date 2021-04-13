import requests
from bs4 import BeautifulSoup
import re
import json
import datetime
from telegram import Update
from telegram.ext import Updater
import re

#dev -1001468852318, prod: -1001219068606
modef = open('mode', 'r')
mode = modef.read().strip()
modef.close()
if mode == 'dev':
    chat_id = '@ota_lounas_dev'
elif mode == 'prod':
    chat_id = '@otalounas'

log_chat_id = '@ota_lounas_dev'

tf = open('token', 'r')
token = tf.read().strip()
tf.close()

weekday_names = ['Maanantai', 'Tiistai', 'Keskiviikko', 'Torstai', 'Perjantai', 'Lauantai', 'Sunnuntai']

def get_page():
    r = requests.get('https://ravintolapalvelut.iss.fi/espoon-tietokyla')
    return r.text

def get_lunch_foods(week):
    ret =  {}
    html = get_page()
    soup = BeautifulSoup(html, 'html.parser')
    h2 = soup.find('h2', string=re.compile(f'Lukio.* lounaslista .* {week}'))
    art = h2.next_sibling
    while (art.name == None):
        art = art.next_sibling
    divs = art.find_all('div', class_='lunch-menu__day')
    for div in divs:
        date = div.find('h2')
        weekday = date.string
        weekday = weekday.strip()
        ret[weekday] = []
        foods  = div.find_all('p')
        for food in foods:
            foodstr = food.string.strip()
            foodstr = foodstr.replace(u'\xa0', u' ')
            if(foodstr != ''):
                ret[weekday].append(foodstr)
    return ret
    
def get_lunch_today():
    date_now = datetime.date.today()
    day = date_now.day
    month = date_now.month
    week = date_now.isocalendar()[1]
    weekday = date_now.weekday()
    weekday_name = weekday_names[weekday]

    weekfoods = get_lunch_foods(week)
    
    foods_candidates = [value for key, value in weekfoods.items() if re.search(weekday_name, key, re.IGNORECASE)]

    if not len(foods_candidates) == 1:
        raise Exception(f"Invalid foods_candidates: {foods_candidates}")

    foods = foods_candidates[0]

    humandate = f"{weekday_name} {day}.{month}"

    return foods, humandate

def bot_start():
    updater = Updater(token)
    return updater

def format_message(foods, weekday):
    ret = "*"
    ret += weekday.replace('.', '\.')
    ret += "*\n"
    for food in foods:
        ret += "\- "
        ret += food.replace('.', '\.').replace('-', '\-')
        ret += "\n"
    return ret

updater = bot_start()


try:
    foods, humandate = get_lunch_today()
except Exception as error:
    date_now = datetime.date.today()
    if date_now.isoweekday() < 6:
        updater.bot.send_message(chat_id=log_chat_id, text="Couldn't send message: "+str(error))
else:
    message = format_message(foods, humandate)
    date_now = datetime.date.today()
    if date_now.isoweekday() < 6:
        updater.bot.send_message(chat_id=chat_id, text=message, parse_mode='MarkdownV2')

updater.stop()
