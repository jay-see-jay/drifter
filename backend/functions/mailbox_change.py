from typing import List

from cloudevents.http import CloudEvent

from services import Gmail, Clerk, OpenAI
from stubs import ParsedMessage, ParsedMessageHeaders
from repositories import UserRepo, ThreadRepo


def handle_mailbox_change(cloud_event: CloudEvent) -> None:
    cloud_event_data = Gmail.decode_cloud_event(cloud_event)

    email = cloud_event_data['emailAddress']
    user_repo = UserRepo()
    user = user_repo.get_user_by_email(email)
    oauth = Clerk().get_oauth_token(user.clerk_user_id)

    history_id = user_repo.get_latest_history_id(user)
    gmail = Gmail(user, oauth)
    history_list = gmail.get_history(history_id)

    if len(history_list) > 0:
        gmail.process_history(history_id, history_list)

    thread_repo = ThreadRepo(user)

    openai = OpenAI()

    inbox_thread_ids = thread_repo.get_inbox()
    for thread_id in inbox_thread_ids:
        thread_messages = thread_repo.get_thread_messages(thread_id)
        if len(thread_messages) == 0:
            continue

        last_message_from = thread_messages[-1]['message_from']
        message_subject = thread_messages[0]['message_subject']
        if user.email in last_message_from:
            continue

        messages: List[ParsedMessage] = []
        for message in thread_messages:
            message_from = message['message_from']
            message_to = message['message_to']

            decoded_body = Gmail.decode_bytes(message['body_data'])
            clean_message = openai.extract_message(decoded_body)
            if not clean_message:
                break
            message_headers: ParsedMessageHeaders = {
                'email_from': message_from,
                'email_to': message_to,
                'subject': message_subject,
            }

            messages.append(ParsedMessage(
                headers=message_headers,
                body=clean_message
            ))

        draft_reply = openai.get_draft_reply(messages)
        if not draft_reply:
            break
        recipient = messages[-1]['headers']['email_from']
        print('Adding draft reply.')
        draft = gmail.create_draft(draft_reply, recipient, thread_id)
        # TODO : draft.message - store as message
        # TODO : Extract and store headers
        # TODO : Extract and store labels
        # TODO : Extract and store message parts


if __name__ == "__main__":
    test_attributes = {
        'specversion': '1.0',
        'type': 'google.cloud.pubsub.topic.v1.messagePublished',
        'source': '//pubsub.googleapis.com/projects/',
        'datacontenttype': 'application/json',
        'time': '2023-10-13T12:00:14.631Z'
    }
    test_data = {
        'message': {
            'data': 'eyJlbWFpbEFkZHJlc3MiOiIxMDNqY2pAZ21haWwuY29tIiwiaGlzdG9yeUlkIjoxMjU3NzZ9',
        },
    }

    test_cloud_event = CloudEvent.create(test_attributes, test_data)
    handle_mailbox_change(test_cloud_event)
