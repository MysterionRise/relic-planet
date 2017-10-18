#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import httplib2
import os
import io
import csv

from telegram.ext import Updater, CommandHandler
from telegram.ext.dispatcher import run_async

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from apiclient.http import MediaIoBaseDownload

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

teams = ["Delonte West", "Вино физрука Jоповичя", "why not?", "Smokin Ducks", "Скан-Тим", "Секта Свидетелей", "WSG", "50 лет без побед", "d.a.m.n. team", "Florida Magic", "-=BallBangers=-", "Трабловики 2017-18"]

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
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

@run_async
def itaka(bot, update):
	chat_id = update.message.chat.id
	file_id = '1iltpcolP3b-wb4w3eROVsByF4Mqy4gDt8BJExmjzGtw'
	credentials = get_credentials()
	http = credentials.authorize(httplib2.Http())
	drive_service = discovery.build('drive', 'v3', http=http)
	print(drive_service.files().get(fileId=file_id).execute())
	request = drive_service.files().export_media(fileId=file_id,
                                             mimeType='text/csv')
	fh = io.FileIO("forecast.csv", 'wb')
	downloader = MediaIoBaseDownload(fh, request)
	done = False
	while done is False:
	    status, done = downloader.next_chunk()

	# reading the csv
	reader = csv.reader(open(r"forecast.csv"),delimiter=',')
	filtered = filter(lambda x: x[1] in teams, list(reader))
	
	print("Total Today Week Transfers Team")
	for row in filtered:
		print("{} {} {} {} {}".format(row[4], row[5], row[9], row[14], row[1]))
	csv.writer(open(r"result.csv",'w'),delimiter=' ').writerows(filtered)
	bot.send_message(chat_id, text="")

def main():	
	updater = Updater("")

        updater.dispatcher.add_handler(CommandHandler('itaka', itaka))
        updater.start_polling()
        updater.idle()	
	
if __name__ == '__main__':
    main()
