#!/usr/bin/env python

from __future__ import print_function
import httplib2
import os

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

import datetime
import time
import calendar
import PyPDF2
import re
import urllib2
from StringIO import StringIO

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'MIT Z Center Google Calendar - Basketball'

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
                                   'calendar-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
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

def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    calId = '8d0imqpqlg6e2gk5o21ri7mqjs@group.calendar.google.com'
    currentEvents = pdfToList()
    firstTimeInPdf = createEvent(currentEvents[0])['start']['dateTime']
    eventsResult = service.events().list(
        calendarId=calId, timeMin=firstTimeInPdf, singleEvents=True,
        orderBy='startTime').execute()
    oldEvents = eventsResult.get('items', [])
    for e in oldEvents:
        service.events().delete(calendarId=calId, eventId=e['id']).execute()
    
    for e in currentEvents:
        event = createEvent(e)
        print(event)
        service.events().insert(calendarId=calId, body=event).execute()


def createEvent(eventInfo):
    timezone_offset = calendar.timegm(time.gmtime()) - calendar.timegm(time.localtime())
    ymdDate = ymd(eventInfo[0])
    militaryStart = mil(eventInfo[1])
    militaryEnd = mil(eventInfo[2])
    startDateTime = ymdDate+'T'+militaryStart+'-04:00'
    endDateTime = ymdDate+'T'+militaryEnd+'-04:00'
    event = {
      'summary': eventInfo[3],
      'start': {
        'dateTime': startDateTime
      },
      'end': {
        'dateTime': endDateTime
        #'dateTime': '2016-01-30T17:00:00-05:00',
      }
    }
    return event

def ymd(date):
    '''
    Friday, January 24, 2016  ====> 2016-01-30
    '''
    l = date.split(' ')
    months = ['January','February','March','April','May','June','July','August','September','October','November','December']
    m = str(months.index(l[1])+1)
    if len(m)<2: m = '0'+m
    d = l[2][:-1]
    y = l[3]
    return y+'-'+m+'-'+d
def mil(t):
    m = str(datetime.datetime.strptime(t, '%I:%M %p'))
    return m[11:]

def pdfToList():
    events = []
    url = 'http://web.mit.edu/athletics/www/recschedule.pdf'
    remoteFile = urllib2.urlopen(urllib2.Request(url)).read()
    memoryFile = StringIO(remoteFile)
    pdfReader = PyPDF2.PdfFileReader(memoryFile)
    t = ''
    for i in range(pdfReader.getNumPages()):
        pageObj = pdfReader.getPage(i)
        t+=pageObj.extractText()
    datePattern = '([A-Z][a-z]*\,\s[A-Za-z]*[0-9]*\s[0-9]*\,\s[0-9]{4})'
    days = re.split(datePattern,t)
    days.pop(0)
    i = 0
    while i<len(days)-1:
        pattern = '[1]?[0-9]\:[0-9]*\s*[AP]M\s*[0-9]?[0-9]\:[0-9]*\s[AP]MDAPER\s*[\(\)\.\&\,\sA-Za-z]*\-Basketball[A-Za-z\s]*[1-2]?'
        result = re.findall(pattern, days[i+1])
        for item in result:
            timePattern = '[1]?[0-9]\:[0-9]*\s*[AP]M'
            times = re.findall(timePattern,item)
            start = times[0]
            end = times[1]
            places = ['DU PONT CT1','DU PONT CT2','Rockwell MAIN COURT']
            for place in places:
                if place in item:
                    location = place
            events.append([days[i],start,end,location])
        i+=2
    return events



if __name__ == '__main__':
    main()

