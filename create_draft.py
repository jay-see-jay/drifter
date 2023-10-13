from email.message import EmailMessage

import base64
import os
import openai

from dotenv import load_dotenv
from googleapiclient.errors import HttpError

from services.gmail import Gmail
from stubs.gmail import *
from stubs.openai import *

load_dotenv()

# #########
# UTILITIES
# #########


# #### ##
# OPEN AI
# #### ##

# Configure openai
openai.api_key = os.getenv('OPENAI_API_KEY')


def instantiate_choice_message(message: dict) -> ChatCompletionMessage:
    return ChatCompletionMessage(
        role=message.get('role'),
        content=message.get('content'),
    )


def instantiate_completion(response: dict) -> ChatCompletion:
    response_choices = response.get('choices', [])
    response_choices = [
        ChatCompletionChoices(
            index=choice.get('index'),
            message=instantiate_choice_message(choice.get('message')),
            finish_reason=choice.get('finish_reason'),
        )
        for choice in response_choices
    ]
    return ChatCompletion(
        id=response.get('id'),
        object=response.get('object'),
        created=response.get('created'),
        model=response.get('model'),
        choices=response_choices,
        usage=response.get('usage')
    )


def extract_message(message: str) -> str:
    prompt = 'Please extract only the new message from the email below, removing any quotes from earlier in the chain:'
    message = [
        {
            'role': 'user',
            'content': f"""
                {prompt}
                {message}
            """
        }
    ]
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=message,
        )

        completion = instantiate_completion(response)

        return completion.choices[0].message.content

    except Exception as e:
        print(f'Issue with converting conversation to json object: {e}')


class MessageHeaders:
    def __init__(self,
                 email_from: str,
                 email_to: str,
                 subject: str,
                 ) -> None:
        self.email_from = email_from
        self.email_to = email_to
        self.subject = subject


class Message:
    def __init__(self,
                 index: int,
                 headers: MessageHeaders,
                 body: str,
                 ):
        self.index = index
        self.headers = headers
        self.body = body


def get_draft_reply(conversation: List[Message]) -> str:
    messages = [
        {
            'role': 'system',
            'content': """
                You are managing my email inbox for me and drafting replies to new emails.
                Each response should only contain the content of the message to send, and nothing else.
                Please don't indicate that you are an AI in anyway. Everything you draft will be checked
                by me before it is sent.
            """
        }
    ]
    for message in conversation:
        role = 'assistant' if message.headers.email_from == 'me' else 'user'
        content = message.body
        messages.append({
            'role': role,
            'content': content,
        })

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )

        completion = instantiate_completion(response)

        return completion.choices[0].message.content

    except Exception as e:
        print(f'Issue getting a draft reply to the conversation: {e}')


# #####
# GMAIL
# #####

gmail_service = Gmail().api


# Get list of threads from Gmail
def get_gmail_thread_ids() -> List[str]:
    try:
        response = gmail_service.users().threads().list(userId='me', maxResults=1).execute()
        threads = response.get('threads', [])
        return [thread['id'] for thread in threads]
    except HttpError as e:
        print(f"Failed to get a list of threads from Gmail: {e}")


def instantiate_message_part(message_part: dict) -> GmailMessagePart:
    headers = message_part.get('headers', [])
    parts = message_part.get('parts', [])
    body = message_part.get('body')

    return GmailMessagePart(
        part_id=message_part.get('partId'),
        mime_type=message_part.get('mimeType'),
        filename=message_part.get('filename'),
        headers=[
            GmailHeader(
                name=header.get('name'),
                value=header.get('value')
            ) for header in headers
        ],
        body=GmailMessagePartBody(
            attachment_id=body.get('attachmentId'),
            size=body.get('size'),
            data=body.get('data'),
        ),
        parts=[instantiate_message_part(part) for part in parts],
    )


def instantiate_message(message: dict) -> GmailMessage:
    return GmailMessage(
        id=message.get('id'),
        thread_id=message.get('threadId'),
        label_ids=message.get('labelIds'),
        snippet=message.get('snippet'),
        history_id=message.get('historyId'),
        internal_date=message.get('internalDate'),
        payload=instantiate_message_part(message.get('payload')),
        size_estimate=message.get('sizeEstimate'),
        raw=message.get('raw')
    )


def instantiate_gmail_message_list(response: dict) -> List[GmailMessage]:
    messages = response.get('messages', [])
    return [instantiate_message(message) for message in messages]


def get_gmail_thread(thread_id: str) -> GmailThread:
    try:
        response = gmail_service.users().threads().get(userId='me', id=thread_id).execute()
        messages = instantiate_gmail_message_list(response)
        return GmailThread(
            id=response.get('id'),
            snippet=response.get('snippet'),
            history_id=response.get('historyId'),
            messages=messages
        )
    except HttpError as e:
        print(f'Failed to get thread from Gmail: {e}')


def create_gmail_draft(draft: str, recipient: str, thread_id: str):
    message = EmailMessage()

    message.set_content(draft)

    message['To'] = recipient
    message['From'] = my_email

    # encoded message
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {
        'message': {
            'threadId': thread_id,
            'raw': encoded_message,
        }
    }

    try:
        draft = gmail_service.users().drafts().create(userId="me", body=create_message).execute()
        print(f'Draft id: {draft["id"]}\nDraft message: {draft["message"]}')

    except HttpError as e:
        print(f'Failed to create draft in Gmail: {e}')


# ##### #######
# EMAIL PARSING
# ##### #######

def body_has_data(body: GmailMessagePartBody) -> bool:
    return body and body.size > 0


def is_container_mime_message_part(payload: GmailMessagePart) -> bool:
    mime_type = payload.mimeType
    return mime_type and mime_type.startswith('multipart/')


def decode_bytes(data: bytes) -> str:
    try:
        return base64.urlsafe_b64decode(data).decode('utf-8')
    except Exception as e:
        print(f'An error occurred while decoding: {e}')


def decode_body(body: GmailMessagePartBody) -> str:
    return decode_bytes(body.data)


def parse_message_part(message_part: GmailMessagePart, body: List[str]) -> None:
    if is_container_mime_message_part(message_part):
        child_message_parts = message_part.parts
        for child_part in child_message_parts:
            parse_message_part(child_part, body)
    else:
        message_body = message_part.body
        mime_type = message_part.mimeType
        if body_has_data(message_body) and mime_type == 'text/plain':
            decoded_data = decode_body(message_body)
            body.append(decoded_data)


my_email = os.getenv('MY_EMAIL')


def check_for_my_email(email: str) -> str:
    if email.find(my_email) >= 0:
        return 'me'
    else:
        return email


def parse_message_headers(message_part: GmailMessagePart) -> MessageHeaders:
    # TODO: Try to extract pure email address only
    headers = message_part.headers
    email_to = ''
    email_from = ''
    subject = ''
    for header in headers:
        if header.name == 'To':
            email_to = check_for_my_email(header.value)
        elif header.name == 'From':
            email_from = check_for_my_email(header.value)
        elif header.name == 'Subject':
            subject = header.value

    return MessageHeaders(email_from, email_to, subject)


def parse_thread(thread_id):
    thread = get_gmail_thread(thread_id)
    count = 0
    messages: List[Message] = []
    for message in thread.messages:
        message_part = message['payload']

        message_headers = parse_message_headers(message_part)

        message_body_list: List[str] = []
        parse_message_part(message_part, message_body_list)
        message_body = ''.join(message_body_list)
        message_body = extract_message(message_body)

        messages.append(Message(
            index=count,
            headers=message_headers,
            body=message_body
        ))
        count += 1

    draft_reply = get_draft_reply(messages)

    recipient = messages[-1].headers.email_from
    create_gmail_draft(draft_reply, recipient, thread_id)


# ####
# MAIN
# ####

def main():
    thread_ids = get_gmail_thread_ids()
    for thread_id in thread_ids:
        parse_thread(thread_id)


if __name__ == '__main__':
    main()
