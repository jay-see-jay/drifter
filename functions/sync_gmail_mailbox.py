import os
from typing import Dict, Set

from dotenv import load_dotenv

from services.gmail import Gmail
from repositories import *
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
        # TODO : Remove 1 thread limit
        threads_list_response = gmail.get_threads(page_token=page_token, count=1)
        thread_ids = threads_list_response['thread_ids']
        gmail.get_threads_by_ids(thread_ids, process_thread_response)
        # TODO : Uncomment
        # next_page_token = threads_list_response.get('nextPageToken', None)
        next_page_token = None
        if next_page_token:
            page_token = next_page_token
        else:
            break

    label_messages: Dict[str, Set[str]] = dict()
    message_parts: List[GmailMessagePart] = []
    headers: List[GmailHeader] = []

    def process_message_part(
        part: GmailMessagePart,
        parent_message_id: str,
    ):
        headers.extend(part.headers)
        message_parts.append(part)
        child_parts = part.parts
        if child_parts:
            for child_part in child_parts:
                process_message_part(child_part, parent_message_id)

    messages: List[GmailMessage] = []
    for thread_id in threads:
        thread = threads.get(thread_id)  # type: GmailThread

        messages.extend(thread.messages)

        for msg in thread.messages:  # type: GmailMessage
            # Process labels
            for label_id in msg.label_ids:  # type: str
                if label_id not in label_messages:
                    label_messages[label_id] = set()

                label_messages[label_id].add(msg.message_id)

            # Process payload / message part(s)
            process_message_part(msg.payload, msg.message_id)

    label_ids = [label_id for label_id in label_messages]
    labels: List[GmailLabel] = []

    def process_label_response(response_id: str, response: dict, exception):
        if exception is not None:
            print(f'Response ID: {response_id} - failed to get label.\n{exception}')
        else:
            labels.append(GmailLabel(
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
            ))

    # TODO: Batch this into groups of 50 labels
    gmail.get_labels(label_ids=label_ids, callback=process_label_response)

    thread_repo = ThreadRepo()
    thread_repo.create_many(threads.values(), user)

    label_repo = LabelRepo()
    label_repo.create_many(labels, user)
    saved_labels = label_repo.get(user)

    message_repo = MessageRepo()
    message_repo.create_many(messages, user)
    message_repo.store_labels(label_messages, saved_labels)

    message_parts_repo = MessagePartRepo()
    message_parts_repo.create_many(message_parts, user)

    header_repo = HeaderRepo()
    header_repo.create_many(headers, user)


if __name__ == "__main__":
    handle_sync_gmail_mailbox({})
