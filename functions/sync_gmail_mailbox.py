import mysql.connector
from flask import Request, Response, make_response
from werkzeug.exceptions import HTTPException
from typing import Dict, Set
from services.gmail import Gmail
from repositories import *
from models.user import User
from stubs.gmail import *
from utilities.general import process_message_part, create_label_messages_dict


def handle_sync_gmail_mailbox(request: Request) -> Response:
    user_repo = UserRepo()
    user: User
    try:
        user = user_repo.get_from_request(request)
    except mysql.connector.Error as e:
        return make_response(e.msg, 404)
    except HTTPException as e:
        return make_response(e.description, 400)

    gmail = Gmail(user)
    page_token = None
    threads: Dict[str, GmailThread] = dict()

    # Can maybe reply to this to explain batching requests to Gmail API?
    # https://stackoverflow.com/questions/26004335/get-multiple-threads-by-threadid-in-google-apps-scripts-gmailapp-class
    while True:
        threads_list_response = gmail.get_threads(page_token=page_token)
        thread_ids = threads_list_response.get('thread_ids', [])
        threads.update(gmail.get_threads_by_ids(set(thread_ids)))
        next_page_token = threads_list_response.get('next_page_token', None)
        if next_page_token:
            page_token = next_page_token
        else:
            break

    label_messages: Dict[str, Set[str]] = dict()
    message_parts: List[GmailMessagePart] = []
    headers: List[GmailHeader] = []
    messages: List[GmailMessage] = []

    for t_id in threads:
        t = threads[t_id]
        messages.extend(t.messages)

        for msg in t.messages:
            # Process labels
            for label_id in msg.label_ids:  # type: str
                if label_id not in label_messages:
                    label_messages[label_id] = set()

                label_messages[label_id].add(msg.message_id)

            # Process payload / message part(s)
            part_headers, part_child_parts = process_message_part(msg.payload)
            headers.extend(part_headers)
            message_parts.extend(part_child_parts)

    label_ids = [label_id for label_id in label_messages]
    labels = gmail.get_labels(label_ids=label_ids)

    thread_repo = ThreadRepo()
    thread_repo.create_many(list(threads.values()), user)

    label_repo = LabelRepo(user)
    label_repo.create_many(labels)
    saved_labels = label_repo.get_all()

    message_repo = MessageRepo(user)
    message_repo.create_many(messages)
    message_repo.store_labels(label_messages, saved_labels)

    message_parts_repo = MessagePartRepo()
    message_parts_repo.create_many(message_parts, user)

    header_repo = HeaderRepo()
    header_repo.create_many(headers, user)

    return make_response()
