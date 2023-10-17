from typing import List

from cloudevents.http import CloudEvent

from services.gmail import Gmail
from services.openai import OpenAI
from repositories.user import UserRepo

from stubs.internal import ParsedMessage


def handle_watch_gmail_messages(cloud_event: CloudEvent) -> None:
    cloud_event_data = Gmail.decode_cloud_event(cloud_event)

    email = cloud_event_data['emailAddress']
    history_id = cloud_event_data["historyId"]

    user = UserRepo().get(email)
    gmail = Gmail(user)
    openai = OpenAI()
    changed_thread_ids = gmail.get_changed_thread_ids(history_id)

    for thread_id in changed_thread_ids:
        thread = gmail.get_thread_by_id(thread_id)

        count = 0
        messages: List[ParsedMessage] = []
        for message in thread['messages']:
            message_part = message['payload']

            message_headers = gmail.parse_message_headers(message_part)

            message_body_list: List[str] = []
            gmail.parse_message_part(message_part, message_body_list)
            message_body = ''.join(message_body_list)
            message_body = openai.extract_message(message_body)

            messages.append(ParsedMessage(
                index=count,
                headers=message_headers,
                body=message_body
            ))

            count += 1

        draft_reply = openai.get_draft_reply(messages)
        recipient = messages[-1]['headers']['email_from']
        gmail.create_draft(draft_reply, recipient, thread['id'])


if __name__ == "__main__":
    test_attributes = {
        'specversion': '1.0',
        'id': '8872658318367077',
        'source': '//pubsub.googleapis.com/projects/jayseejay-1/topics/gmail-change',
        'type': 'google.cloud.pubsub.topic.v1.messagePublished',
        'datacontenttype': 'application/json',
        'time': '2023-10-13T12:00:14.631Z'
    }
    test_data = {
        'message': {
            'data': 'eyJlbWFpbEFkZHJlc3MiOiIxMDNqY2pAZ21haWwuY29tIiwiaGlzdG9yeUlkIjoxMjU3NzZ9',
            'messageId': '8872658318367077',
            'message_id': '8872658318367077',
            'publishTime': '2023-10-13T12:00:14.631Z',
            'publish_time': '2023-10-13T12:00:14.631Z'
        },
        'subscription': 'projects/jayseejay-1/subscriptions/eventarc-europe-west2-watch-gmail-messages-176919-sub-793'
    }

    test_cloud_event = CloudEvent.create(test_attributes, test_data)
    handle_watch_gmail_messages(test_cloud_event)
