import os
from typing import Dict, Set, Tuple
from datetime import datetime

from dotenv import load_dotenv

from services.gmail import Gmail
from repositories.user import UserRepo
from repositories.label import LabelRepo
from repositories.thread import ThreadRepo
from repositories.message import MessageRepo
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
            threads[response['id']] = GmailThread(
                thread_id=response.get('id'),
                history_id=response.get('historyId'),
                messages=response.get('messages'),
                snippet=response.get('snippet'),
            )

    # Can maybe reply to this to explain batching requests to Gmail API?
    # https://stackoverflow.com/questions/26004335/get-multiple-threads-by-threadid-in-google-apps-scripts-gmailapp-class
    while True:
        threads_list_response = gmail.get_threads(page_token=page_token, count=1)
        thread_ids = threads_list_response['thread_ids']
        gmail.get_threads_by_ids(thread_ids, process_thread_response)
        # next_page_token = threads_list_response.get('nextPageToken', None)
        next_page_token = None
        if next_page_token:
            page_token = next_page_token
        else:
            break

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
            process_message_part(message_part, parent_message_id, message_part_id)

    messages: List[GmailMessage] = []
    for thread_id in threads:
        thread = threads.get(thread_id)  # type: GmailThread

        messages.extend(thread.messages)

        for message in thread.messages:  # type: GmailMessage
            # Process labels
            for label_id in message.label_ids:  # type: str
                if label_id not in label_messages:
                    label_messages[label_id] = set()

                label_messages[label_id].add(message.message_id)

            # Process payload / message part(s)
            process_message_part(message.payload, message.message_id)

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

    # TODO [x] Save all `threads` to db
    thread_repo = ThreadRepo()
    thread_repo.create_many(threads.values(), user)
    # TODO [x] Save all `labels` to db
    label_repo = LabelRepo()
    label_repo.create_many(labels, user)
    # TODO [x] Add messages to db
    message_repo = MessageRepo()
    message_repo.create_many(messages, user)
    # TODO [ ] Add message parts to db
    # TODO [ ] Add headers to db


if __name__ == "__main__":
    handle_sync_gmail_mailbox({})
