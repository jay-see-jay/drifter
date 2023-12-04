import functions_framework
from firebase_functions import identity_fn
from flask import Request, Response

from cloudevents.http import CloudEvent

import functions


@functions_framework.cloud_event
def mailbox_change(cloud_event: CloudEvent) -> None:
    functions.handle_mailbox_change(cloud_event)


@functions_framework.http
def sync_gmail(request: Request) -> Response:
    return functions.handle_sync_gmail(request)


@functions_framework.cloud_event
def refresh_mailbox_sub(cloud_event: CloudEvent) -> None:
    functions.handle_refresh_mailbox_sub()


@functions_framework.http
def watch_gmail(request: Request) -> Response:
    return functions.handle_watch_gmail(request)


@identity_fn.before_user_created(region="europe-west2", max_instances=10)
def create_user(event: identity_fn.AuthBlockingEvent) -> None:
    functions.handle_create_user(event)
