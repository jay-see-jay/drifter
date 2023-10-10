from typing import List

import base64
import os
import openai

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from stubs.gmail import GmailThread

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# #### ##
# OPEN AI
# #### ##

# Configure openai
openai.organization = os.getenv('OPENAI_ORG_ID')
openai.api_key = os.getenv('OPENAI_API_KEY')


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


def get_gmail_thread(thread_id: str) -> GmailThread:
    try:
        response = gmail_service.users().threads().get(userId='me', id=thread_id).execute()
        return GmailThread(
            id=response.get('id'),
            snippet=response.get('snippet'),
            history_id=response.get('historyId'),
            messages=response.get('messages', []),
        )
    except HttpError as e:
        print(f"Failed to get thread from Gmail: {e}")


# ##### #######
# EMAIL PARSING
# ##### #######

def body_has_data(body) -> bool:
    return body and body.get('size', 0) > 0


def is_container_mime_message_part(payload) -> bool:
    mime_type = payload.get('mimeType')  # type: str
    return mime_type.startswith('multipart/')


def decode_bytes(data):
    try:
        return base64.urlsafe_b64decode(data).decode('utf-8')
    except Exception as e:
        print(f"An error occurred while decoding: {e}")


def decode_body(body) -> str:
    return decode_bytes(body['data'])


def parse_message_part(message_part):
    if is_container_mime_message_part(message_part):
        child_message_parts = message_part.get('parts', [])
        for child_part in child_message_parts:
            parse_message_part(child_part)
    else:
        message_body = message_part.get('body')
        mime_type = message_part.get('mimeType')
        if body_has_data(message_body) and mime_type == 'text/plain':
            decoded_data = decode_body(message_body)
            print(decoded_data)


def parse_thread(thread_id):
    thread = get_gmail_thread(thread_id)
    count = 1
    for message in thread.messages:
        print(f"Message: {count}")
        message_part = message.get('payload')
        parse_message_part(message_part)
        count += 1


def main():
    thread_ids = get_gmail_thread_ids()
    for thread_id in thread_ids:
        parse_thread(thread_id)


if __name__ == '__main__':
    main()
