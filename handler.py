from datetime import datetime
import main as Email2SlackBot

# entry point for Lambda
def lambda_handler(event, context):
    print 'Running at', unicode(datetime.now())
    Email2SlackBot.main()
    print 'Finished running at', unicode(datetime.now())
