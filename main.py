import base64
import json

from cloudevents.http import CloudEvent
import functions_framework


def get_value_or_fail(data: dict, key: str) -> str:
    value = data.get('key')
    if not value:
        raise Exception(f'Could not extract {key}')
    else:
        return value


# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.cloud_event
def watch_gmail_messages(cloud_event: CloudEvent) -> None:
    cloud_event_data = base64.b64decode(cloud_event.data["message"]["data"]).decode()
    cloud_event_data = json.loads(cloud_event_data)

    user_email = get_value_or_fail(cloud_event_data, 'emailAddress')
    history_id = get_value_or_fail(cloud_event_data, 'historyId')

    print('user_email', user_email)
    print('history_id', history_id)
