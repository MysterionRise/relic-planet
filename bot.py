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

from telegram.ext import Updater, CommandHandler
from telegram.ext.dispatcher import run_async

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

teams = ["Delonte West", "Вино физрука Jоповичя", "why not?", "Smokin Ducks", "Скан-Тим", "Секта Свидетелей", "WSG",
         "50 лет без побед", "d.a.m.n. team", "Florida Magic", "-=BallBangers=-", "Трабловики 2017-18"]

try:
    import argparse

    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Drive API Python Quickstart'


def get_today_data_for_players():
    r = requests.get('http://nbafantasy.center/')
    html = bs4.BeautifulSoup(r.text, "html.parser")
    today_scores = {}
    scores = html.find_all('td', {'class': "player-score"})
    names = html.find_all('td', {'class': "player-name"})
    for i in range(len(names)):
        today_scores[names[i].get_text()] = int(scores[i].get_text())
    #df = pd.read_csv(open('data', 'rb'))
    #for index, row in df.iterrows():
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


def get_all_sheets():
    file_id = '1iltpcolP3b-wb4w3eROVsByF4Mqy4gDt8BJExmjzGtw'
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    drive_service = discovery.build('drive', 'v3', http=http)
    request = drive_service.files().export(fileId=file_id,
                                           mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp = request.execute(http=http)
    file = open("forecast.xlsx", "wb")
    file.write(resp)


def read_players_sheet():
    df = pd.read_excel(open('forecast.xlsx', 'rb'), 'Players')
    history_data = dict(zip(df['Player'], df['PPG']))
    today_data = get_today_data_for_players()
    diff = []
    for key, value in today_data.items():
        if key.strip(' ') in history_data:
            ppg = history_data[key.strip(' ')]
            pr = tuple((key, float(ppg) - float(value)))
            diff.append(pr)
    # todo filter only players that we have on sports.ru
    # [x for x in my_list if x.attribute == value]
    diff.sort(key=lambda x: x[1])
    return (diff[0], diff[len(diff) - 1])


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'drive-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def read_last_name():
    if os.path.exists('lastname') > 0:
        with open('lastname', 'r') as f:
            lines = f.readlines()
            return lines[0]
    return ''

def save_last_name(name):
    with open('lastname', 'w') as f:
        f.write(name)

prev_name = read_last_name()
last_injury_date = datetime.datetime.now() - datetime.timedelta(days=2)

npy = 'worst_players'

def read_worst_players():
    if os.path.exists(npy) > 0:
        with open(npy, 'rb') as pickle_file:
            return pickle.load(pickle_file)
    return {}

def save_worst_players(players):
    with open(npy, 'wb') as pickle_file:
        pickle.dump(players, pickle_file)

worst_players = read_worst_players()

@run_async
def injury_report(bot, update):
    try:
        chat_id = update.message.chat.id
        r = requests.get('http://www.rotoworld.com/teams/injuries/nba/all/')
        html = bs4.BeautifulSoup(r.text, "html.parser")
        reports = html.find_all('div', {'class': "report"})
        print(len(reports))
        impacts = html.find_all('div', {'class': "impact"})
        print(len(impacts))
        dates = html.find_all('div', {'class': "date"})
        print(len(dates))
        report = []
        for i in range(len(reports)):
            # my_date = datetime.datetime.strptime(row['date'], "%Y-%m-%d")
            report.append((reports[i].get_text(), impacts[i + 1].get_text(),
                           datetime.datetime.strptime(str(datetime.datetime.now().year) + " " + dates[i].get_text(),
                                                      "%Y %b %d")
                           ))
        report.sort(key=lambda x: x[2], reverse=True)
        # [i for i in j if i >= 5]
        z = [i for i in report if i[2] > last_injury_date]
        report_msg = ""
        for report in z:
            report_msg += report[0] + " " + report[1] + " " + report[2].strftime('%d, %b %Y') + "\n"
        msgs = [report_msg[i:i + 4000] for i in range(0, len(report_msg), 4000)]
        for text in msgs:
            bot.send_message(chat_id, text="<pre>" + text + "</pre>", parse_mode='HTML')

    except Exception as e:
        print(e)


@run_async
def itaka(bot, job):
    try:
        print("polling changes from Google Drive")
        chat_id = "-1001140113988"
        file_id = '1iltpcolP3b-wb4w3eROVsByF4Mqy4gDt8BJExmjzGtw'
        credentials = get_credentials()
        http = credentials.authorize(httplib2.Http())
        drive_service = discovery.build('drive', 'v3', http=http)
        current_name = drive_service.files().get(fileId=file_id).execute()["name"]

        global prev_name
        if current_name != prev_name:
            print("we should call itaka")
            prev_name = current_name
            request = drive_service.files().export(fileId=file_id, mimeType='text/csv')
            resp = request.execute(http=http)
            file = open("forecast.csv", "wb")
            file.write(resp)
            # get all sheets
            get_all_sheets()
            # split xslx and read sheet & convert to csv
            best, worst = read_players_sheet()

            print("reading csv")
            # reading the csv
            with open('forecast.csv', encoding='utf-8') as f:
                reader = csv.reader(f)
                filtered = filter(lambda x: x[1] in teams, reader)
                worst_players[str(datetime.datetime.now().date())] = worst[0]
                print(worst_players)
                save_worst_players(worst_players)
                itaka = "<b>Pidor dnya: {} {}\n".format(worst[0], -worst[1])
                itaka += "Reverse dnya: {} +{}</b>\n".format(best[0], -best[1])
                itaka += "\n"
                itaka += "<b>Total Today Diff Week Transfers RemainingGames Team </b>\n<pre>"
                for row in filtered:
                    itaka += "{} {} {} {} {} {} {}\n".format(row[4], row[5], row[3], row[9], row[14], row[13], row[1])
                itaka += "</pre>"
                print("Ready to send message to chatland")
                save_last_name(current_name)
                msg = bot.send_message(chat_id, text=itaka, parse_mode='HTML')
                bot.pin_chat_message(chat_id, msg.message_id)

    except Exception as e:
        print(e)

@run_async
def worst_player_report(bot, update):
    try:
        worst_players = read_worst_players()
        v = {}
        for key, value in worst_players.items():
            v[value] = v.get(value, 0) + 1
        message = ""
        for f, s in sorted(v.items(), key=lambda x: x[1], reverse=True):
            message += "{} - {}\n".format(f, s)
        print(message)
        update.message.reply_text(message, parse_mode='HTML')
    except Exception as e:
        print(e)


def main():
    updater = Updater("")

    updater.dispatcher.add_handler(CommandHandler('pidorReport', worst_player_report))

    job = updater.job_queue
    job.run_repeating(itaka, interval=300, first=0)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
