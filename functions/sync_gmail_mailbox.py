import os
from typing import Dict, Set, Tuple
from datetime import datetime

from dotenv import load_dotenv

from services.gmail import Gmail
from models.user import User
from repositories.user import UserRepo
from stubs.gmail import GmailThread, GmailMessage

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
        threads_list_response = gmail.get_threads(next_page_token=page_token)
        thread_ids = [thread['id'] for thread in threads_list_response['threads']]
        gmail.get_threads_by_ids(thread_ids, process_thread_response)
        next_page_token = threads_list_response.get('nextPageToken', None)
        if next_page_token:
            page_token = next_page_token
        else:
            break

    thread_values: Set[Tuple[str, str | None, str, int]] = set()
    message_values: Set[Tuple[str, str, int, str, str, datetime, str, int, str, datetime, str, str]] = set()

    for thread_id in threads:
        thread = threads[thread_id]  # type: GmailThread
        thread_messages = thread['messages']
        # (id, snippet, history_id, user_pk)
        thread_values.add((
            thread['id'],
            thread.get('snippet'),
            thread['historyId'],
            user.pk
        ))

        for message in thread_messages:  # type: GmailMessage
            # (id, snippet, user_pk, thread_id, history_id, internal_date, size_estimate, ra)
            message_values.add((
                message['id'],
                message.get('snippet'),
                user.pk,
                thread['id'],
                message['historyId'],
                message['internalDate'],
                message['sizeEstimate'],
                message['raw']
            ))

            # TODO : Process message headers, body and payload


if __name__ == "__main__":
    handle_sync_gmail_mailbox({})
