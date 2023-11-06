import functions_framework
from flask import Request, Response

from cloudevents.http import CloudEvent

from functions.watch_gmail_messages import handle_watch_gmail_messages
from functions.sync_gmail_mailbox import handle_sync_gmail_mailbox


@functions_framework.cloud_event
def watch_gmail_messages(cloud_event: CloudEvent) -> None:
    handle_watch_gmail_messages(cloud_event)


@functions_framework.http
def sync_gmail_mailbox(request: Request) -> Response:
    return handle_sync_gmail_mailbox(request)
