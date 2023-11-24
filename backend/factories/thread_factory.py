from models import *
from stubs import GmailThreadResponse


def create_thread(user: User, thread_response: GmailThreadResponse) -> Thread:
    messages = [
        Message(
            message_id=thread_message.get('id'),
            label_ids=thread_message.get('labelIds'),
            snippet=thread_message.get('snippet'),
            history_id=thread_message.get('historyId'),
            internal_date=thread_message.get('internalDate'),
            size_estimate=thread_message.get('sizeEstimate'),
            payload=thread_message.get('payload'),
        )
        for thread_message in thread_response.get('messages', [])
    ]
    return Thread(
        user=user,
        thread_id=thread_response.get('id'),
        history_id=thread_response.get('historyId'),
        snippet=thread_response.get('snippet'),
        messages=messages,
    )
