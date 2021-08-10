import requests
from bs4 import BeautifulSoup
import re
import datetime
from telegram import Update
from telegram.ext import Updater
import re

foods = None

url_list = [
    'https://ravintolapalvelut.iss.fi/espoon-tietokyla/otaniemen-lukio-vko-',
    'https://ravintolapalvelut.iss.fi/espoon-tietokyla/lukiolaisten-lounaslista-vko-',
    'https://ravintolapalvelut.iss.fi/espoon-tietokyla/lukion-lounas-vko-',
]

weekday_names = ['Maanantai', 'Tiistai', 'Keskiviikko',
                 'Torstai', 'Perjantai', 'Lauantai', 'Sunnuntai']


def get_frontpage():
    r = requests.get('https://ravintolapalvelut.iss.fi/espoon-tietokyla')
    return r.text

def get_lunch_foods(week):
    print("Getting lunch foods")
    r = get_lunch_foods_frontpage(week)
    if r == None:
        print("Trying url")
        r = get_lunch_foods_url(week, week)
    if r == None:
        print("Trying bruteforce")
        r = get_lunch_foods_url_bruteforce(week)
    if r == None:
        print("Didn't find lunch foods...")
    else:
        print("Found lunch foods: ")
        print(r)
    return r


def get_url_page(week, i=0):
    base_url = url_list[i]
    r = requests.get(f'{base_url}{week}')
    if r.status_code == 404:
        i += 1
        if i >= len(url_list):
            return None
        return get_url_page(week, i)
    return r.text


def get_lunch_foods_frontpage(week):
    r = {}
    html = get_frontpage()
    soup = BeautifulSoup(html, 'html.parser')
    h2 = soup.find('h2', string=re.compile(
        f'(Lukio.* ?|Otaniemen ?|lounas.* ?|lounaslista.* ?|[Ll]ukio.* ?){{1,2}}[\s\S]*(vko|viikko)[\s\S]*{week}[\s\S]*'))
    if h2 == None:
        return None
    art = h2.next_sibling
    if art == None:
        return None
    while (art.name == None):
        art = art.next_sibling
        if art == None:
            return None
    divs = art.find_all('div', class_='lunch-menu__day')
    for div in divs:
        date = div.find('h2')
        weekday = date.string
        weekday = weekday.strip()
        r[weekday] = []
        foods = div.find_all('p')
        for food in foods:
            foodstr = food.string.strip()
            foodstr = foodstr.replace(u'\xa0', u' ')
            if(foodstr != ''):
                r[weekday].append(foodstr)
    return r


def get_lunch_foods_url(week, i):
    r = {}
    html = get_url_page(i)
    if html == None:
        return None
    soup = BeautifulSoup(html, 'html.parser')
    content = soup.find('div', class_='article__body')
    title = soup.find('h1', class_='article__title',
                      string=re.compile(f'(Otaniemen ?|lounas.* ?|lounaslista.* ?|[Ll]ukio.* ?){{1,2}}[\s\S]*(vko|viikko)[\s\S]*{week}[\s\S]*'))
    if not title:
        print("no title found")
        return None
    foodtitles = content.findAll('h2', class_='article__heading--h2')
    for ftitle in foodtitles:
        foods = []
        weekday = ftitle.text
        for sib in ftitle.find_next_siblings():
            if not sib.name == 'p':
                break
            foods.append(sib.text)
        r[weekday] = foods
    return r


def get_lunch_foods_url_bruteforce(week):
    for i in range(0, 52):
        r = get_lunch_foods_url(week, i)
        if r:
            return r
    return None


def get_day_message():
    global foods
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

    humandate = f"{weekday_name} {day}.{month}"

    return format_day_message(foodlist, humandate)


def format_day_message(foodlist, humandate):
    r = "*"
    r += humandate.replace('.', '\.')
    r += "*\n"
    for food in foodlist:
        r += "\- "
        r += food.replace('.', '\.').replace('-', '\-')
        r += "\n"
    return r

def get_week_message():
    global foods
    if not foods:
        raise Exception("No foods")
    date_now = datetime.date.today()
    week = date_now.isocalendar()[1]
    r = f"*Viikko {week}*\n"
    for weekday, foodlist in foods.items():
        r += format_day_message(foodlist, weekday)
    return r

def load_foods(*args, **kwargs):
    global foods
    date_now = datetime.date.today()
    week = date_now.isocalendar()[1]
    foods = get_lunch_foods(week)