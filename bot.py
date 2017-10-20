#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import httplib2
import os
import csv

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


prev_name = ""


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
            # reading the csv
            with open('forecast.csv', encoding='utf-8') as f:
                reader = csv.reader(f)
                filtered = filter(lambda x: x[1] in teams, reader)
                itaka = "<b>Total Today Diff Week Transfers RemainingGames Team </b>\n<pre>"
                for row in filtered:
                    itaka += "{} {} {} {} {} {} {}\n".format(row[4], row[5], row[3], row[9], row[14], row[13], row[1])
                itaka += "</pre>"
                msg = bot.send_message(chat_id, text=itaka, parse_mode='HTML')
                bot.pin_chat_message(chat_id, msg.message_id)

    except Exception as e:
        print(e)


def main():
    updater = Updater("")

    job = updater.job_queue
    job.run_repeating(itaka, interval=300, first=0)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
