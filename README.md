# Email2SlackBot
Checks IMAP server for new mail and posts it in a Slack channel 

#How to use:
1. Create a new Incoming Webhook custom integration for your Slack channel (https://slack.com/apps/A0F7XDUAZ-incoming-webhooks)
2. `$ git clone https://github.com/isiah-lloyd/Email2SlackBot.git`
3. `$ virtualenv venv`
4. `$ source venv/bin/activate`
5. `$ pip install -r requirements.txt`
6. Enter your Webhook URL from Slack into the `settings.example.ini` file along with your email server configuration
7. Rename `settings.example.ini` to `settings.ini`
8. `$ python main.py`
9. The program is now setup and will check for new mail and post it to slack on subsequent runs
10. Run `python main.py` using a cron job

Do not modify `last_uid.txt` created by the program but if you are encountering issues it maybe a good idea to regenerate the file by deleting it.

#Current problems:
Does not escape markdown in subject or body

## Storage Options

By default, the bot stores the last uid in `last_uid.txt` on your local machine. However, by setting `storage_location = s3` and setting `aws_access_key_id`, `aws_secret_access_key`, and `aws_s3_bucket_name` in your `settings.ini` you can use Amazon S3 for storage.
