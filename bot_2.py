import random
import time
import telebot
import requests
from textblob import TextBlob
from telebot import types
from bs4 import BeautifulSoup
from selenium import webdriver

chromedriver = 'chromedriver'
options = webdriver.ChromeOptions()
# options.add_argument('headless')  # для открытия headless-браузера
browser = webdriver.Chrome(executable_path=chromedriver, options=options)
# апи бота
bot = telebot.TeleBot('1862518301:AAHodQbwuteEFY-pku81mPsuhqsWHmB_b2Q')
# меню бота
keyboard1 = telebot.types.ReplyKeyboardMarkup(True, True)
keyboard1.row('Расписание электричек')
# keyboard1.row('Расписание станции')
keyboard1.row('Успею ли я на электричку?')
url = ''
data = ''


# Обработка команды /start
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Привет, ' + message.chat.first_name +
                     '\nЗдесь ты можешь найти всю интересующую тебя информации по поводу движения поездов',
                     reply_markup=keyboard1)
    print(message.chat)
    print(message.chat.first_name)


# Обработка команды /help
@bot.message_handler(commands=['help'])
def help_message(message):
    bot.send_message(
        message.chat.id,
        'Для начала работы с ботом нажмите /start или /menu.\n' +
        'В меню вы можете выбрать различные маршруты и станции для поиска расписания электричек.\n' +
        'Dсе станции вводить с большой буквы, на русском языке и без пробелов'
    )


# Обработка команды /menu
@bot.message_handler(commands=['menu'])
def menu_message(message):
    bot.send_message(message.chat.id, 'Открываю меню...', reply_markup=keyboard1)


# Обработка присланных сообщений
@bot.message_handler(content_types=['text'])
def send_text(message):
    if message.text.lower() == 'расписание электричек':
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton('Москва', callback_data='get-M'),
            telebot.types.InlineKeyboardButton('Санкт-Петербург', callback_data='get-P')
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton('Другой город', callback_data='get-A')
        )
        bot.send_message(message.chat.id, 'Выеберете нужный вам город:', reply_markup=keyboard)
    elif message.text.lower() == 'расписание станции':
        bot.send_message(message.chat.id, 'Введите название станции: ')
        global url
        url = 'https://www.tutu.ru/prigorod/'
        bot.register_next_step_handler(message, get_station)
    elif message.text.lower() == 'успею ли я на электричку?':
        bot.send_message(message.chat.id, 'Калькулирую вероятность...')
        time.sleep(5)
        bot.send_message(message.chat.id, 'Осталось совсем чуть-чуть')
        time.sleep(3)
        bot.send_message(message.chat.id, 'Еще немного....')
        time.sleep(2)
        bot.send_message(message.chat.id, 'Получилось!')
        bot.send_message(message.chat.id, 'Я считаю, что шанс вашего успеха равен - ' + str(random.randint(1, 100)) + '%')
    else:
        bot.send_message(message.chat.id, 'Я вас не понял, повторите сообщение')


def get_station(message):
    global Station
    Station = message.text
    st = TextBlob(Station)
    print(url)
    browser.get(url)
    sbox = browser.find_element_by_class_name('j-input_field')
    sbox.send_keys(Station)
    bot.send_message(message.chat.id, 'Начинаю поиск расписания станции ' + Station + ': ')
    sbox = browser.find_elements_by_class_name('b-button__standart')[3]
    sbox.click()
    browser.find_elements_by_tag_name('li')[27].click()
    response = requests.get(browser.current_url)
    soup = BeautifulSoup(response.text, 'lxml')
    trs = soup.find_all('tr', class_='')
    for tr in trs:
        print(tr)
        print(tr.txt)


def start_search(message):
    global Station1
    Station1 = message.text
    bot.send_message(message.chat.id, 'Введите конечную станцию')
    bot.register_next_step_handler(message, get_second_st)


def get_second_st(message):
    global Station2
    Station2 = message.text
    bot.send_message(message.chat.id, 'Начинаю поиск расписания маршрута ' + Station1 + ' - ' + Station2)
    st1 = TextBlob(Station1)
    st2 = TextBlob(Station2)
    if data != 'A':
        parse_city(message)
    else:
        parse_any(message)


# Обработка callback_data
@bot.callback_query_handler(func=lambda c: True)
def iq_callback(c):
    global data
    data = c.data
    bot.answer_callback_query(c.id)
    global url
    if data.startswith('get-'):
        data = data[4:]
        if data == 'M':
            url = 'https://www.tutu.ru/msk/'
            bot.send_message(c.message.chat.id, 'Расписании электричек Москвы')
        elif data == 'P':
            url = 'https://www.tutu.ru/spb/'
            bot.send_message(c.message.chat.id, 'Расписании электричек Санкт-Петербурга')
        elif data == 'A':
            url = 'https://www.tutu.ru/'
            bot.send_message(c.message.chat.id, 'Расписание электричек')
        bot.send_message(c.message.chat.id, 'Введите начальную станцию')
        bot.register_next_step_handler(c.message, start_search)


def parse_city(message):
    browser.get(url)
    sbox = browser.find_element_by_id("searchDepartureStationName")
    sbox.send_keys(Station1)
    sbox = browser.find_element_by_id("searchArrivalStationName")
    sbox.send_keys(Station2)
    submit = browser.find_element_by_class_name("rm-form_submit_button").find_element_by_tag_name("button")
    submit.click()
    time.sleep(1)
    print(browser.current_url)
    parse(message, browser.current_url)


def parse_any(message):
    browser.get(url)
    sbox = browser.find_element_by_class_name('tab_etrain')
    sbox.click()
    sbox = browser.find_element_by_name("st1")
    sbox.send_keys(Station1)
    sbox = browser.find_element_by_name("st2")
    sbox.send_keys(Station2)
    submit = browser.find_elements_by_class_name("j-button-submit")[2]
    submit.click()
    time.sleep(1)
    print(browser.current_url)
    parse(message, browser.current_url)


def parse(message, ur):
    response = requests.get(ur)
    soup = BeautifulSoup(response.text, 'lxml')
    trs = soup.find_all('tr', class_='desktop__card__yoy03')
    if trs:
        bot.send_message(message.chat.id, 'Расписание найдено, начинаю вывод:')
        for tr in trs[1:-1]:
            time.sleep(1)
            text = ''
            text += 'Отправление: '
            text += tr.find('td', class_='desktop__depTime__2Ue-g').text
            text += '\nПрибытие: '
            text += tr.find('td', class_='desktop__arrTime__1N9Pw').text
            text += '\nВремя в пути: '
            text += tr.find('td', class_='desktop__range__1Kbxz').text
            text += '\nРежим движения: '
            text += tr.find('td', class_='desktop__interval__2jhPJ').text
            text += '\nМаршрут электрички: '
            text += tr.find('td', class_='desktop__route__37GXG').text
            text += '\nСтоимость: '
            text += tr.find('td', class_='desktop__price__31Jsd').text
            bot.send_message(message.chat.id, text)
        bot.send_message(message.chat.id, 'Вывод расписания закончен')
    else:
        bot.send_message(message.chat.id, 'Ошибка поиска!\nВы ввели неправильную станцию')


bot.polling(none_stop=True)
