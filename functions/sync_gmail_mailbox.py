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

    def process_thread_response(response_id: str, response: dict, exception):
        if exception is not None:
            print(f'Response ID: {response_id} - failed to get thread.\n{exception}')
        else:
            thread = GmailThread(
                thread_id=response.get('id'),
                history_id=response.get('historyId'),
                messages=response.get('messages'),
                snippet=response.get('snippet'),
            )
            threads[response['id']] = thread

    # Can maybe reply to this to explain batching requests to Gmail API?
    # https://stackoverflow.com/questions/26004335/get-multiple-threads-by-threadid-in-google-apps-scripts-gmailapp-class
    while True:
        threads_list_response = gmail.get_threads(next_page_token=page_token, count=1)
        thread_ids = [thread.get('id') for thread in threads_list_response['threads']]
        gmail.get_threads_by_ids(thread_ids, process_thread_response)
        # next_page_token = threads_list_response.get('nextPageToken', None)
        next_page_token = None
        if next_page_token:
            page_token = next_page_token
        else:
            break

    # (id, snippet, user_pk, thread_id, history_id, internal_date, size_estimate, ra)
    message_values: Set[Tuple[str, str, int, str, str, datetime, str, int, str, datetime, str, str]] = set()
    label_messages: Dict[str, Set[str]] = dict()
    # (id, user_pk, message_id, mime_type, body_attachment_id, body_size, body_data, parent_message_part_id)
    message_part_values: Set[Tuple[str, int, str | None, str, str, str, int, str, str | None]] = set()
    # (message_part_id, name, value)
    header_values: Set[Tuple[str, str, str]] = set()

    def process_message_part(
        message_part: GmailMessagePart,
        parent_message_id: str,
        parent_message_part_id: str = None,
    ):
        message_part_id = message_part.get('partId')

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
        thread_messages = thread.messages  # type: List[GmailMessage]

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
                thread.thread_id,
                message.get('historyId'),
                message.get('internalDate'),
                message.get('sizeEstimate'),
                message.get('raw')
            ))

            # Process payload / message part(s)
            payload = message.get('payload')  # type: GmailMessagePart
            process_message_part(payload, message_id)

    label_ids = [label_id for label_id in label_messages]
    labels: List[GmailLabel] = []

    def process_label_response(response_id: str, response: dict, exception):
        if exception is not None:
            print(f'Response ID: {response_id} - failed to get label.\n{exception}')
        else:
            label = GmailLabel(
                label_id=response.get('id'),
                name=response.get('name'),
                label_type=response.get('type'),
                messages_total=response.get('messagesTotal'),
                messages_unread=response.get('messagesUnread'),
                threads_total=response.get('threadsTotal'),
                threads_unread=response.get('threadsUnread'),
                color=response.get('color'),
                message_list_visibility=response.get('messageListVisibility'),
                label_list_visibility=response.get('labelListVisibility')
            )
            labels.append(label)

    gmail.get_labels(label_ids=label_ids, callback=process_label_response)

    # TODO : Save all `threads` to db
    # TODO : Save all `labels` to db


if __name__ == "__main__":
    handle_sync_gmail_mailbox({})
