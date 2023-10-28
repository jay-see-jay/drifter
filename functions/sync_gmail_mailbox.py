import os
from typing import Dict, Set, Tuple
from datetime import datetime

from dotenv import load_dotenv

from services.gmail import Gmail
from repositories.user import UserRepo
from stubs.gmail import *

load_dotenv()


def handle_sync_gmail_mailbox(request):
    user_repo = UserRepo()
    # TODO: Extract user id or email from request
    user = user_repo.get(os.getenv('MY_EMAIL'))

    gmail = Gmail(user)
    page_token = None
    threads: Dict[str, GmailThread] = dict()

    def process_thread_response(response_id: str, response: GmailThread, exception):
        if exception is not None:
            print(f'Response ID: {response_id} - failed to get thread.\n{exception}')
        else:
            threads[response['id']] = response

    # Can maybe reply to this to explain batching requests to Gmail API?
    # https://stackoverflow.com/questions/26004335/get-multiple-threads-by-threadid-in-google-apps-scripts-gmailapp-class
    while True:
        threads_list_response = gmail.get_threads(next_page_token=page_token, count=1)
        thread_ids = [thread['id'] for thread in threads_list_response['threads']]
        gmail.get_threads_by_ids(thread_ids, process_thread_response)
        # next_page_token = threads_list_response.get('nextPageToken', None)
        next_page_token = None
        if next_page_token:
            page_token = next_page_token
        else:
            break

    # (id, snippet, history_id, user_pk)
    thread_values: Set[Tuple[str, str | None, str, int]] = set()
    # (id, snippet, user_pk, thread_id, history_id, internal_date, size_estimate, ra)
    message_values: Set[Tuple[str, str, int, str, str, datetime, str, int, str, datetime, str, str]] = set()
    # TODO : For each label get the details from Gmail, then add to db in labels and messages_labels tables
    # https://developers.google.com/gmail/api/reference/rest/v1/users.labels/get
    label_messages: Dict[str, Set[str]] = dict()
    # (id, user_pk, message_id, mime_type, body_attachment_id, body_size, body_data, parent_message_part_id)
    message_part_values: Set[Tuple[str, int, str | None, str, str, str, int, str, str | None]] = set()
    # (message_part_id, name, value)
    header_values: Set[Tuple[str, str, str]]

    def process_message_part(
        message_part: GmailMessagePart,
        parent_message_id: str,
        parent_message_part_id: str = None,
    ):
        message_part_id = message_part.get('id')

        headers = message_part.get('headers')  # type: List[GmailHeader]
        for header in headers:
            header_values.add((
                message_part_id,
                header.get('name'),
                header.get('value'),
            ))

        body = message_part.get('body')  # type: GmailMessagePartBody
        message_part_values.add((
            message_part_id,
            user.pk,
            parent_message_id,
            message_part.get('mimeType'),
            message_part.get('filename'),
            body.get('attachmentId'),
            body.get('size'),
            body.get('data'),
            parent_message_part_id,
        ))
        parts = message_part.get('parts', [])
        for message_part in parts:
            process_message_part(message_part, message_id, message_part_id)

    for thread_id in threads:
        thread = threads.get(thread_id)  # type: GmailThread
        thread_messages = thread.get('messages')  # type: List[GmailMessage]
        thread_values.add((
            thread.get('id'),
            thread.get('snippet'),
            thread.get('historyId'),
            user.pk
        ))

        for message in thread_messages:  # type: GmailMessage
            message_id = message.get('id')
            # Process labels
            label_ids = message.get('labelIds')  # type: List[str]
            for label_id in label_ids:
                if label_id not in label_messages:
                    label_messages[label_id] = set()

                label_messages[label_id].add(message['id'])

            # Process message
            message_values.add((
                message_id,
                message.get('snippet'),
                user.pk,
                thread.get('id'),
                message.get('historyId'),
                message.get('internalDate'),
                message.get('sizeEstimate'),
                message.get('raw')
            ))

            # Process payload / message part(s)
            payload = message.get('payload')  # type: GmailMessagePart
            process_message_part(payload, message_id)


if __name__ == "__main__":
    handle_sync_gmail_mailbox({})
