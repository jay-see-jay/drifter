import functions_framework

from cloudevents.http import CloudEvent

from functions.watch_gmail_messages import handle_watch_gmail_messages
from functions.sync_gmail_mailbox import handle_sync_gmail_mailbox


# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.cloud_event
def watch_gmail_messages(cloud_event: CloudEvent) -> None:
    handle_watch_gmail_messages(cloud_event)


@functions_framework.http
def sync_gmail_mailbox(request):
    # This must accept a Flask request object as an argument and return
    # a value that Flask can convert into an HTTP response object.
    # https://flask.palletsprojects.com/en/2.1.x/api/#flask.Request
    # https://flask.palletsprojects.com/en/2.1.x/quickstart/#about-responses
    handle_watch_gmail_messages(request)
    return 'Ok'
