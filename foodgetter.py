import json
import requests
from bs4 import BeautifulSoup
import re
import datetime
from telegram import Update
from telegram.ext import Updater
import re

foods = None

restaurantid = 176176

json_url = f"https://www.amica.fi/api/restaurant/menu/week?language=fi&restaurantPageId={restaurantid}&weekDate="

weekday_names = ['Maanantai', 'Tiistai', 'Keskiviikko',
                 'Torstai', 'Perjantai', 'Lauantai', 'Sunnuntai']

def get_json(date):
    """Get html for week, bruteforcing each url"""
    r = requests.get(f'{json_url}{date.strftime("%Y-%m-%d")}')
    if r.status_code != 200:
        return None
    return r.json()

def get_lunch_foods(date):
    print("Getting lunch foods")
    r = get_json(date)
    if not r: return None
    print("Found foods")
    foods = {}
    for menu in r['LunchMenus']:
        day = menu['DayOfWeek']
        dayfoods = []
        for setmenu in menu['SetMenus']:
            ftype = f"{setmenu['Name']}"
            farr = [meal['Name'] + " " + " ".join(meal['Diets']) for meal in setmenu['Meals']]
            if len(farr) > 0:
                dayfoods.append((ftype, farr))
        if len(dayfoods) > 0:
            foods[day] = dayfoods
    return foods

def get_day_message():
    global foods
    if not foods:
        load_foods()
        if not foods:
            raise Exception("No foods")
    date_now = datetime.date.today()
    day = date_now.day
    month = date_now.month
    weekday = date_now.weekday()
    weekday_name = weekday_names[weekday]

    foods_candidates = [value for key, value in foods.items(
    ) if re.search(weekday_name, key, re.IGNORECASE)]

    if not len(foods_candidates) == 1:
        raise Exception(f"Invalid foods_candidates: {foods_candidates}")

    foodlist = foods_candidates[0]

    humandate = f"{weekday_name} {day}.{month}."

    return format_day_message(foodlist, humandate)


def format_day_message(foodlist, humandate):
    r = "*"
    r += humandate.replace('.', '\.').replace('-', '\-')
    r += "*\n"
    for ftype, farr in foodlist:
        r += ftype
        r += ":\n"
        r += "".join([ f'- {x}\n' for x in farr]).replace('.', '\.').replace('-', '\-').replace('*', '\*')
    print(r)
    return r

def get_week_message(isNextWeek=False):
    global foods
    if not foods:
        load_foods()
        if not foods:
            raise Exception("No foods")
    date_now = datetime.date.today()
    if isNextWeek:
        td = datetime.timedelta(weeks=1)
        date_now = date_now + td
    week = date_now.isocalendar()[1]
    r = f"*Viikko {week}*\n"
    for weekday, foodlist in foods.items():
        r += format_day_message(foodlist, weekday)
    return r

def load_foods(isNextWeek=False):
    global foods
    date_now = datetime.date.today()
    if isNextWeek:
        td = datetime.timedelta(weeks=1)
        date_now = date_now + td
    foods = get_lunch_foods(date_now)
    return foods
