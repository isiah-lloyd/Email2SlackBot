import imaplib
import os
from pprint import pprint
import requests
from email.parser import Parser
from email.utils import parsedate_tz, mktime_tz
from ConfigParser import SafeConfigParser

config = SafeConfigParser()
config.read('settings.ini')

#imaplib.Debug = 4 Uncomment for debuging purposes 
def email_connection():
    # Connect to the server
    c = imaplib.IMAP4_SSL(config.get('EMAIL', 'server'), config.get('EMAIL', 'server_port'))
    # Login to our account
    c.login(config.get('EMAIL', 'username'), config.get('EMAIL', 'password'))
    return c
def getNewEmails(last_uid): 
    # Borrowed from Jean-Tiare Le Bigot (https://blog.yadutaf.fr/2013/04/12/fetching-all-messages-since-last-check-with-python-imap/)
    new_messages = 0
    c = email_connection()
    c.select('INBOX', readOnly=True)
    command = "{}:*".format(last_uid)
    result, data = c.uid('search', None, 'UID',  command)
    messages = data[0].split()
    for message_uid in messages:
        # SEARCH command *always* returns at least the most
        # recent message, even if it has already been synced
        if message_uid > last_uid:
            new_messages+= 1
            result, data = c.uid('fetch', message_uid, '(RFC822)')
            emailParser(data[0][1])   
    print "New Messages:", new_messages
    if new_messages:
        print "Saving new UID to file"
        result, data = c.uid('search', None, "ALL")
        last_uid = data[0].split()[-1]
        f = open("last_uid.txt", "w")
        f.write(last_uid)
        f.close()
    c.logout()
def emailParser(raw_email):
        message_raw = raw_email
        msg = Parser().parsestr(message_raw)
        msg_from =  msg['from'][0:]
        msg_subject = msg['subject']
        msg_date = msg['date']
        date_formatted = mktime_tz(parsedate_tz(msg_date))
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                msg_body = part.get_payload()
        #slackWebHook(msg_subject,msg_from,msg_date,msg_body)

def slackWebHook(subject, email_from, date, body):
    payload={"text": "*Subject:* {subject}\n*From:* `{email_from}`\n*Date*: {date}\n--\n{body}".format(subject=subject, email_from=email_from, date=date, body=body)}
    r = requests.post(config.get('SLACK', 'webhook_url'), json = payload)

if __name__ == '__main__':
    if os.path.isfile('last_uid.txt'):
        print "Found last checked UID"
        f = open("last_uid.txt")
        last_uid = f.read()
        getNewEmails(last_uid)
    else:
        print 'Getting UID of first email'
        c = email_connection()
        c.select("INBOX", readOnly=True)
        result, data = c.uid('search', None, "ALL")
        c.logout()
        last_uid = data[0].split()[-1]
        f = open("last_uid.txt", "w")
        f.write(last_uid)
        f.close()
        print 'Run this program again to check for new mail (with a cron job) , if new mail is found it will be posted to slack'

