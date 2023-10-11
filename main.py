from typing import List

import base64
import os
import openai

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from stubs.gmail import GmailThread, GmailMessagePart, GmailMessagePartBody, GmailMessage, GmailHeader

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

load_dotenv()

# #### ##
# OPEN AI
# #### ##

# Configure openai
# openai.organization = os.getenv('OPENAI_ORG_ID')
openai.api_key = os.getenv('OPENAI_API_KEY')


def extract_message(message: str):
    message = [
        {
            'role': 'user',
            'content': f"""
                Can you extract just the new message from the email below,
                removing anything quoted from earlier in the chain?
                {message}
            """
        }
    ]
    try:
        return openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=message,
        )
    except Exception as e:
        print(f'Issue with converting conversation to json object: {e}')


# #####
# GMAIL
# #####

# Configure Gmail service
def get_gmail_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)


gmail_service = get_gmail_service()


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
        print(f"Failed to get thread from Gmail: {e}")


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
        print(f"An error occurred while decoding: {e}")


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


def parse_message_headers(message_part: GmailMessagePart):
    # TODO: Try to extract pure email address only
    headers = message_part.headers
    email_to = ''
    email_from = ''
    for header in headers:
        if header.name == 'To':
            email_to = check_for_my_email(header.value)
        elif header.name == 'From':
            email_from = check_for_my_email(header.value)

    return {
        'from': email_from,
        'to': email_to,
    }


def parse_thread(thread_id):
    thread = get_gmail_thread(thread_id)
    count = 1
    for message in thread.messages:
        message_details = f'Message Index: {count}\n'
        message_part = message.payload
        message_headers = parse_message_headers(message_part)
        message_details += f'Message From: {message_headers.get("from")}\nMessage To: {message_headers.get("to")}\n'
        message_body_list: List[str] = []
        parse_message_part(message_part, message_body_list)
        message_body = ''.join(message_body_list)
        message_details += f'Message Body:\n{message_body}'
        conversation = extract_message(message_body)
        # TODO: Turn conversation into array with relevant information then submit to Open AI for a draft
        print(conversation)
        count += 1


# ####
# MAIN
# ####

def main():
    thread_ids = get_gmail_thread_ids()
    for thread_id in thread_ids:
        parse_thread(thread_id)


if __name__ == '__main__':
    main()
