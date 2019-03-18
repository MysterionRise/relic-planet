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

from telegram.ext import Updater, CommandHandler
from telegram.ext.dispatcher import run_async

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from apiclient.http import MediaIoBaseDownload
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

teams = ["СканТим", "Мамка Дончича", "Нулебал", "Секта Свидетелей", "WSG", "why not?", "Delonte West",
         "Бендер", "OpenAI", "Трабловики 2018-9"]

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


def get_all_sheets():
    file_id = '1iltpcolP3b-wb4w3eROVsByF4Mqy4gDt8BJExmjzGtw'
    credentials = get_credentials()
    drive_service = build('drive', 'v3', credentials=credentials)
    request = drive_service.files().export(fileId=file_id,
                                           mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    fh = io.FileIO("forecast.xlsx", 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()


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


def get_credentials():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


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
        drive_service = build('drive', 'v3', credentials=credentials)
        current_name = drive_service.files().get(fileId=file_id).execute()["name"]

        global prev_name
        if current_name != prev_name:
            print("we should call itaka")
            prev_name = current_name
            request = drive_service.files().export(fileId=file_id, mimeType='text/csv')

            fh = io.FileIO("forecast.csv", 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            # get all sheets
            get_all_sheets()
            # split xslx and read sheet & convert to csv
            # TODO FIX IT
            # best1, best2, best3, worst3, worst2, worst1 = read_players_sheet()

            print("reading csv")
            # reading the csv
            with open('forecast.csv', encoding='utf-8') as f:
                reader = csv.reader(f)
                filtered = filter(lambda x: x[1] in teams, reader)
                # TODO FIX IT
                #worst_players[str(datetime.datetime.now().date())] = worst1[0]
                #print(worst_players)
                #save_worst_players(worst_players)
                #itaka = "<b>Top-3 pidors dnya:\n {} {}\n {} {} \n {} {} \n".format(worst1[0], -worst1[1],
                #                                                                   worst2[0], -worst2[1],
                #                                                                   worst3[0], -worst3[1])
                #itaka += "Reverse dnya: {} +{}</b>\n".format(best1[0], -best1[1])
                #itaka += "\n"
                itaka = "<b>Total Today Diff Week Transfers RemainingGames Team </b>\n<pre>"
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
