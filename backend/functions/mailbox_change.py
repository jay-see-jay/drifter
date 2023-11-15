import json
from typing import List

from cloudevents.http import CloudEvent

from services import Gmail, Clerk
from services.openai import OpenAI
from repositories import UserRepo

from stubs.internal import ParsedMessage


def handle_mailbox_change(cloud_event: CloudEvent) -> None:
    cloud_event_data = Gmail.decode_cloud_event(cloud_event)

    email = cloud_event_data['emailAddress']
    user_repo = UserRepo()
    user = user_repo.get_user_by_email(email)
    oauth = Clerk().get_oauth_token(user.clerk_user_id)

    history_id = user_repo.get_latest_history_id(user)
    print('history_id', history_id)
    gmail = Gmail(user, oauth)
    history_list = gmail.get_history(history_id)

    with open('output.json', 'w') as json_file:
        json.dump(history_list, json_file)

    if len(history_list) > 0:
        gmail.process_history(history_id, history_list)

    return

    openai = OpenAI()

    for thread_id in changed_thread_ids:
        thread = gmail.get_thread(thread_id)

        count = 0
        messages: List[ParsedMessage] = []
        for message in thread.messages:
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
        gmail.create_draft(draft_reply, recipient, thread.id)
