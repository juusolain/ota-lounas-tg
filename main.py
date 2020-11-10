import urllib.request
from bs4 import BeautifulSoup
import re
import json
import datetime
from telegram import Update
from telegram.ext import Updater
from collections import OrderedDict
lunchdata = None

tf = open('token', 'r')
token = tf.read().strip()
tf.close()

def get_page():
    req = urllib.request.urlopen("https://ravintolapalvelut.iss.fi/espoon-tietokyla")
    req_bytes = req.read()

    html = req_bytes.decode("utf8")
    req.close()
    return html

def get_lunch_foods(week):
    ret = OrderedDict()
    html = get_page()
    soup = BeautifulSoup(html, 'html.parser')
    h2 = soup.find('h2', string=f'Lukiolaisten lounaslista vko {week}')
    art = h2.next_sibling
    while (art.name == None):
        art = art.next_sibling
    divs = art.find_all('div', class_='lunch-menu__day')
    for div in divs:
        date = div.find('h2', class_='article__heading--h2')
        datestring = date.string
        datestring = datestring.strip()
        if (datestring[-1] == "."):
            datestring = datestring[:-1]
        compdate = re.search('[0-9]{1,2}\.[0-9]{1,2}', datestring)[0]
        ret[compdate] = {'humandate': datestring, 'foods': []}
        foods  = div.find_all('p')
        for food in foods:
            foodstr = food.string.strip()
            foodstr = foodstr.replace(u'\xa0', u' ')
            if(foodstr != ''):
                ret[compdate]['foods'].append(foodstr)
    return ret
    
def fetch_lunch():
    global lunchdata
    date_now = datetime.date.today()
    year, week_num, day_of_week = date_now.isocalendar()
    lunchdata = get_lunch_foods(week_num)
    
def get_lunch_today():
    global lunchdata
    date_now = datetime.date.today()
    day = date_now.day
    month = date_now.month
    obj = lunchdata[f'{day}.{month}']
    if not obj:
        return None, None

    return obj['foods'], obj['humandate']

def save_lunch():
    global lunchdata
    jsondata = json.dumps(lunchdata, indent=2)
    with open('lunchdata.json', 'w') as f:
        f.write(jsondata)
        f.close()


def load_lunch():
    global lunchdata
    with open('lunchdata.json', 'r') as f:
        jsondata = f.read()
        lunchdata = json.loads(jsondata)
        f.close()

def help_command(update, context):
    update.message.reply_text('Help!')

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
fetch_lunch()
foods, humandate = get_lunch_today()
if foods == None or humandate == None:
    print("Couldn't send message")
else:
    message = format_message(foods, humandate)
    date_now = datetime.date.today()
    if date_now.isoweekday() < 6:
        # prod: -1001219068606, dev: -1001468852318
        updater.bot.send_message(chat_id=-1001468852318, text=message, parse_mode='MarkdownV2')

updater.stop()
