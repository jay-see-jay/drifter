from __future__ import print_function

import base64
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from stubs.gmail import GmailThreadsListResponse

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def get_gmail_threads_response(response: dict) -> GmailThreadsListResponse:
    return GmailThreadsListResponse(
        threads=response.get('threads'),
        next_page_token=response.get('nextPageToken'),
        result_estimate_size=response.get('resultEstimateSize'),
    )


def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
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

    try:
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().threads().list(userId='me', maxResults=1).execute()
        threads_response = get_gmail_threads_response(results)

        for thread in threads_response.threads:
            tdata = service.users().threads().get(userId='me', id=thread['id']).execute()
            for message in tdata['messages']:
                message_parts = message['payload']['parts']
                for part in message_parts:

                    def decode_bytes(data):
                        try:
                            return base64.urlsafe_b64decode(data).decode('utf-8')
                        except Exception as e:
                            print(f"An error occurred while decoding: {e}")

                    decoded_part = decode_bytes(part['body']['data'])

                    print(decoded_part)

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    main()
