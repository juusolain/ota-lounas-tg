import json
import requests
from bs4 import BeautifulSoup
import re
import datetime
from telegram import Update
from telegram.ext import Updater
import re

foods_stored = None
foods_stored_week = None

restaurantid = 330303

debug_override_date = None#datetime.date.fromisoformat("2022-01-11")

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
    foods = {}
    for menu in r['LunchMenus']:
        day = menu['DayOfWeek']
        dayfoods = []
        school_food_exists = any("lukio" in f"{setmenu['Name']}".lower() for setmenu in menu['SetMenus'])
        for setmenu in menu['SetMenus']:
            ftype = f"{setmenu['Name']}"
            if "henkilöstö" in ftype.lower() or (school_food_exists and not "lukio" in ftype.lower()):
                continue
            farr = [meal['Name'] + " " + " ".join(meal['Diets']) for meal in setmenu['Meals']]
            if len(farr) > 0:
                dayfoods.append((ftype, farr))
        if len(dayfoods) > 0:
            foods[day] = dayfoods
    print("Found foods")
    print(foods)
    return foods

def get_day_message():
    global foods_stored
    if not foods_stored:
        load_foods()
        if not foods_stored:
            raise Exception("No foods")
    date_now = debug_override_date or datetime.date.today()
    day = date_now.day
    month = date_now.month
    weekday = date_now.weekday()
    weekday_name = weekday_names[weekday]

    foods_candidates = [value for key, value in foods_stored.items(
    ) if re.search(weekday_name, key, re.IGNORECASE)]

    if len(foods_candidates) > 1:
        raise Exception(f"Invalid foods_candidates: {foods_candidates}")
    if len(foods_candidates) == 0:
        return None
    

    foodlist = foods_candidates[0]

    humandate = f"{weekday_name} {day}.{month}."

    return format_day_message(foodlist, humandate)


def format_day_message(foodlist, humandate):
    r = "*"
    r += humandate.replace('.', '\.').replace('-', '\-')
    r += "*\n"
    for ftype, farr in foodlist:
        r += "".join([ f'- {x}\n' for x in farr]).replace('.', '\.').replace('-', '\-').replace('*', '\*')
    return r

def get_week_message(isNextWeek=False):
    global foods_stored, foods_stored_week
    if not foods_stored:
        load_foods(isNextWeek=isNextWeek)
        if not foods_stored:
            raise Exception("No foods")
    date_now = debug_override_date or datetime.date.today()
    if isNextWeek:
        td = datetime.timedelta(weeks=1)
        date_now = date_now + td
    r = f"*Viikko {foods_stored_week}*\n"
    for weekday, foodlist in foods_stored.items():
        r += format_day_message(foodlist, weekday)
    return r


def manual_set_foods(new_foods, isNextWeek=False):
    global foods_stored, foods_stored_week
    date_now = debug_override_date or datetime.date.today()
    if isNextWeek:
        td = datetime.timedelta(weeks=1)
        date_now = date_now + td
    new_foods_week = date_now.isocalendar()[1]
    if new_foods or not foods_stored_week or foods_stored_week < new_foods_week:
        foods_stored = new_foods
        foods_stored_week = new_foods_week
    else:
        print('Got invalid foods, using old stored foods')
    return foods_stored

def load_foods(isNextWeek=False):
    global foods_stored, foods_stored_week
    date_now = debug_override_date or datetime.date.today()
    if isNextWeek:
        td = datetime.timedelta(weeks=1)
        date_now = date_now + td
    new_foods = get_lunch_foods(date_now)
    new_foods_week = date_now.isocalendar()[1]
    if new_foods or not foods_stored_week or foods_stored_week < new_foods_week:
        foods_stored = new_foods
        foods_stored_week = new_foods_week
    else:
        print('Got invalid foods, using old stored foods')
    return foods_stored
