import imaplib
import os
from datetime import datetime
from pprint import pprint
import requests
from email.parser import Parser
from email.utils import parsedate_tz, mktime_tz
from ConfigParser import SafeConfigParser
import boto3

config = SafeConfigParser()
if os.path.isfile('settings.ini'):
    config.read('settings.ini')
else:
    print 'No settings.ini file found... will attempt to use environment variables instead'

# pull in keys
AWS_ACCESS_KEY_ID = os.environ.get('aws_access_key_id') or config.get('AWS', 'aws_access_key_id')
AWS_SECRET_ACCESS_KEY = os.environ.get('aws_secret_access_key') or config.get('AWS', 'aws_secret_access_key')
AWS_S3_BUCKET_NAME = os.environ.get('aws_s3_bucket_name') or config.get('AWS', 'aws_s3_bucket_name')
STORAGE_LOCATION = os.environ.get('storage_location') or config.get('STORAGE', 'storage_location')

EMAIL_SERVER = os.environ.get('server') or config.get('EMAIL', 'server')
EMAIL_SERVER_PORT = os.environ.get('server_port') or config.get('EMAIL', 'server_port')
EMAIL_USERNAME = os.environ.get('username') or config.get('EMAIL', 'username')
EMAIL_PASSWORD = os.environ.get('password') or config.get('EMAIL', 'password')

WEBHOOK_URL = os.environ.get('webhook_url') or config.get('SLACK', 'webhook_url')

# setup s3 client
s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)


#imaplib.Debug = 4 Uncomment for debuging purposes 
def email_connection():
    # Connect to the server
    c = imaplib.IMAP4_SSL(EMAIL_SERVER, EMAIL_SERVER_PORT)
    # Login to our account
    c.login(EMAIL_USERNAME, EMAIL_PASSWORD)
    return c

def getNewEmails(last_uid): 
    # Borrowed from Jean-Tiare Le Bigot (https://blog.yadutaf.fr/2013/04/12/fetching-all-messages-since-last-check-with-python-imap/)
    new_messages = 0
    c = email_connection()
    c.select('INBOX', readonly=True)
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
        set_last_uid(last_uid)
    c.logout()

def emailParser(raw_email):
        message_raw = raw_email
        msg = Parser().parsestr(message_raw)
        msg_from =  msg['from'][0:]
        msg_subject = msg['subject']
        msg_date = msg['date']
        date_epoch = mktime_tz(parsedate_tz(msg_date))
        msg_body = ""
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                msg_body = part.get_payload()
        slackWebHook(msg_subject,msg_from,date_epoch,msg_date,msg_body)

def slackWebHook(subject, email_from, date_epoch,date_header, body):
    payload={"text": "*Subject:* {subject}\n*From:* `{email_from}`\n*Date*: <!date^{date_epoch}^{{date}} at {{time}}|{date_header}>\n--\n{body}".format(subject=subject, email_from=email_from, date_epoch=date_epoch, date_header=date_header, body=body)}
    r = requests.post(WEBHOOK_URL, json = payload)

# get last_uid from storage location
def get_last_uid():
    if STORAGE_LOCATION == 's3':
        # s3 storage
        obj = s3_client.get_object(Bucket=AWS_S3_BUCKET_NAME, Key='last_uid.txt')
        last_uid = obj['Body'].read().decode('utf-8')
        return last_uid
    else:
        # local storage
        f = open("last_uid.txt")
        last_uid = f.read()
        return last_uid

# set last_uid in storage location
def set_last_uid(value):
    if STORAGE_LOCATION == 's3':
        # s3 storage
        s3_client.put_object(Body=value, Bucket=AWS_S3_BUCKET_NAME, Key='last_uid.txt')
    else:
        # local storage
        f = open("last_uid.txt", "w")
        f.write(value)
        f.close()

# checks if last_uid.txt exists
def last_uid_file_exists():
    if STORAGE_LOCATION == 's3':
        # s3 storage
        try:
            s3_client.get_object(Bucket=AWS_S3_BUCKET_NAME, Key='last_uid.txt')
        except:
            return False

        return True
    else:
        # local storage
        return os.path.isfile('last_uid.txt')


def main():
    if last_uid_file_exists():
        print "Found last checked UID"
        last_uid = get_last_uid()
        getNewEmails(last_uid)
    else:
        print 'Getting UID of first email'
        c = email_connection()
        c.select("INBOX", readonly=True)
        result, data = c.uid('search', None, "ALL")
        c.logout()
        last_uid = data[0].split()[-1]
        set_last_uid(last_uid)
        print 'Run this program again to check for new mail (with a cron job) , if new mail is found it will be posted to slack'


if __name__ == '__main__':
    main()
