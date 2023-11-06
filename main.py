import functions_framework
from flask import Request, Response

from cloudevents.http import CloudEvent

import functions


@functions_framework.cloud_event
def watch_gmail_messages(cloud_event: CloudEvent) -> None:
    functions.handle_watch_gmail_messages(cloud_event)


@functions_framework.http
def sync_gmail_mailbox(request: Request) -> Response:
    return functions.handle_sync_gmail_mailbox(request)


@functions_framework.http
def watch_gmail_mailbox(request: Request) -> Response:
    return functions.handle_watch_gmail_mailbox(request)
