import functions_framework

from cloudevents.http import CloudEvent

from functions.watch_gmail_messages import handle_watch_gmail_messages


# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.cloud_event
def watch_gmail_messages(cloud_event: CloudEvent) -> None:
    handle_watch_gmail_messages(cloud_event)


if __name__ == '__main__':
    print('Hi')
