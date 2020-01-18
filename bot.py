#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import httplib2
import os
import csv
import requests
import bs4
import pandas as pd
import datetime
import os.path
import pickle
import sys
import io
import atexit

from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram.ext.dispatcher import run_async

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


def get_today_data_for_players():
    options = Options()
    options.add_argument('--headless')

    driver = webdriver.Firefox(options=options)
    driver.get('http://nbafantasy.center/')
    scores = driver.find_elements_by_css_selector('td[class~="player-score"]')
    names = driver.find_elements_by_css_selector('td[class~="player-name"]')
    today_scores = {}
    for i in range(len(names)):
        if scores[i].text:
            print(scores[i].text)
            print(names[i].text)
            today_scores[names[i].text] = int(scores[i].text)
    # df = pd.read_csv(open('data', 'rb'))
    # for index, row in df.iterrows():
    #    if index % 2 == 0:
    #        today_scores[row['name']] = int(row['score'])
    return today_scores


def get_players_by_link():
    # class ="stat-table fantasy-table"
    # class="name-td
    r = requests.get('https://www.sports.ru/fantasy/basketball/team/424989.html')
    html = bs4.BeautifulSoup(r.text, "html.parser")
    td = html.find_all('div', {'class': "basket-field"})
    for p in td:
        print(p)


def get_file_name(file_link):
    r = requests.get(file_link)
    d = r.headers['content-disposition']
    return d


def read_players_sheet():
    try:
        df = pd.read_excel(open('forecast.xlsx', 'rb'), 'Players')
        ppg_data = dict(zip(df['Sports.ru'], df['PPG']))
        total_data = dict(zip(df['Sports.ru'], df['Points']))
        today_data = get_today_data_for_players()
        diff = []
        for key, value in today_data.items():
            if key.strip(' ') in ppg_data:
                ppg = float(ppg_data[key.strip(' ')])
                total = float(total_data[key.strip(' ')])
                if total != 0 and ppg != 0 and total / ppg > 1:
                    number_of_games = total / ppg
                    correct_ppg = ((total - float(value)) / (number_of_games - 1))
                else:
                    correct_ppg = 0
                pr = tuple((key, float(correct_ppg) - float(value)))
                diff.append(pr)
        # todo filter only players that we have on sports.ru
        # [x for x in my_list if x.attribute == value]
        print(diff)
        diff.sort(key=lambda x: x[1])
        return diff[0], diff[1], diff[2], diff[len(diff) - 3], diff[len(diff) - 2], diff[len(diff) - 1]
    except Exception as inst:
        print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
        print(type(inst))  # the exception instance
        print(inst.args)  # arguments stored in .args


lastname_config = 'lastname'


def read_last_name(config=lastname_config):
    if os.path.exists(config) > 0:
        with open(config, 'r') as f:
            lines = f.readlines()
            return lines[0]
    return ''


def save_last_name(name, config=lastname_config):
    with open(config, 'w') as f:
        f.write(name)


prev_name = read_last_name()

chat_ids_config = 'chat_ids'


def read_chat_ids():
    if os.path.exists(chat_ids_config) > 0:
        with open(chat_ids_config, 'rb') as pickle_file:
            return pickle.load(pickle_file)
    return []


def save_chat_ids(chat_ids):
    with open(chat_ids_config, 'wb') as pickle_file:
        pickle.dump(chat_ids, pickle_file)


chat_ids = read_chat_ids()

teams_by_chat_id_config = 'teams_by_chat_id'


def read_teams_by_chat_id():
    if os.path.exists(teams_by_chat_id_config) > 0:
        with open(teams_by_chat_id_config, 'rb') as pickle_file:
            return pickle.load(pickle_file)
    return {}


def save_teams_by_chat_id(teams_by_chat_id):
    with open(teams_by_chat_id_config, 'wb') as pickle_file:
        pickle.dump(teams_by_chat_id, pickle_file)


teams_by_chat_id = read_teams_by_chat_id()


def eligble_for_report(chat_id, current_name):
    name = read_last_name(chat_id)
    if name != current_name:
        return True
    return False


@run_async
def itaka(context):
    try:
        print("polling changes from Google Drive")
        file_link = 'https://docs.google.com/spreadsheets/d/1iltpcolP3b-wb4w3eROVsByF4Mqy4gDt8BJExmjzGtw/export?format=csv'
        current_name = get_file_name(file_link)

        global prev_name
        global chat_ids
        global teams_by_chat_id
        if current_name != prev_name:
            print("we should download fresh file")
            r = requests.get(file_link)
            prev_name = current_name
            with open('forecast.csv', 'wb') as f:
                f.write(r.content)

            save_last_name(current_name)
            save_chat_ids(chat_ids)
            save_teams_by_chat_id(teams_by_chat_id)

            # reading the csv

        print("we should try to call itaka for chats: {}".format(chat_ids))
        for chat_id in chat_ids:
            print(chat_id)
            if eligble_for_report("chat_" + str(chat_id), current_name):
                teams = teams_by_chat_id[chat_id]
                if len(teams) > 0:
                    with open('forecast.csv', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        filtered = filter(lambda x: x[1] in teams, reader)
                        itaka = "<b>Total Today Diff Week Transfers RemainingGames Team </b>\n<pre>"
                        for row in filtered:
                            itaka += "{} {} {} {} {} {} {}\n".format(row[4], row[5], row[3], row[9], row[14], row[13],
                                                                     row[1])
                        itaka += "</pre>"
                        print("Ready to send message to {}".format(chat_id))
                        save_last_name(current_name, config="chat_" + str(chat_id))
                        msg = context.bot.send_message(chat_id, text=itaka, parse_mode='HTML')
                        context.bot.pin_chat_message(chat_id, msg.message_id)

    except Exception as e:
        print(e)


@run_async
def start_callback(update, context):
    update.message.reply_text("Добро пожаловать в Чятленд Фэнтази Бот!")
    chat_ids.append(update.message.chat.id)
    teams_by_chat_id[update.message.chat.id] = []


@run_async
def add_team_callback(update, context):
    teams_by_chat_id[update.message.chat.id].append(" ".join(context.args))
    update.message.reply_text("Добавляем команду {} в ежедневный отчет".format(" ".join(context.args)))

@run_async
def stop_callback(update, context):
    teams_by_chat_id
    update.message.reply_text("Спасибо за пользование ботом для отчетов")

@run_async
def help_callback(update, context):
    update.message.reply_text(
        text="""
        <b>Команды Чятленд Фэнтази Бота:</b>
        
        Если вы хотите получить полную поддержку функционала - дайте боту возможность закреплять сообщения!
        
        /start - зарегистрировать чат для ежедневного отчета
        /help - показать справку
        /addTeam имя команды - добавить команду к ежедневному отчету
        /stop - прекратить получать ежедневные отчеты
        """, parse_mode='HTML'
    )


@atexit.register
def goodbye():
    save_chat_ids(chat_ids)
    save_teams_by_chat_id(teams_by_chat_id)
    print('exiting...')


def main():
    updater = Updater("", use_context=True)

    updater.dispatcher.add_handler(CommandHandler('help', help_callback))
    updater.dispatcher.add_handler(CommandHandler('start', start_callback))
    updater.dispatcher.add_handler(CommandHandler('addTeam', add_team_callback))
    updater.dispatcher.add_handler(CommandHandler('stop', stop_callback))

    job = updater.job_queue
    job.run_repeating(itaka, interval=600, first=0)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
