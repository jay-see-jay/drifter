import os

from dotenv import load_dotenv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from stubs.gmail import *

load_dotenv()

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose',
]


class Gmail:
    @staticmethod
    def _get_user_auth() -> dict:
        return {
            "token": os.getenv('TEMP_TOKEN'),
            "refresh_token": os.getenv('TEMP_REFRESH_TOKEN'),
            "token_uri": os.getenv('GOOGLE_TOKEN_URI'),
            "client_id": os.getenv('GOOGLE_CLIENT_ID'),
            "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
            "scopes": SCOPES,
            "expiry": os.getenv('TEMP_TOKEN_EXPIRY')
        }

    @staticmethod
    def _get_credentials() -> dict:
        return {
            "web": {
                "client_id": os.getenv('GOOGLE_CLIENT_ID'),
                "project_id": os.getenv('GOOGLE_PROJECT_ID'),
                "auth_uri": os.getenv('GOOGLE_AUTH_URI'),
                "token_uri": os.getenv('GOOGLE_TOKEN_URI'),
                "auth_provider_x509_cert_url": os.getenv('GOOGLE_AUTH_PROVIDER'),
                "client_secret": os.getenv('GOOGLE_CLIENT_SECRET')
            }
        }

    def __init__(self):
        # creds = None
        # TODO: Replace logic that checked for a token.json file
        token_dict = self._get_user_auth()
        creds = Credentials.from_authorized_user_info(token_dict, SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                creds_dict = self._get_credentials()
                flow = InstalledAppFlow.from_client_config(
                    creds_dict, SCOPES)
                creds = flow.run_local_server()
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        self.api = build('gmail', 'v1', credentials=creds)

    def get_history(self, start_history_id='125125'):
        try:
            return self.api.users().history().list(userId='me', startHistoryId=start_history_id).execute()
        except HttpError as e:
            print(f'Failed to get history of mailbox changes: {e}')

    def watch_mailbox(self) -> WatchSubscriptionResponse:
        cloud_project = os.getenv('GOOGLE_PROJECT_ID')
        pubsub_topic = os.getenv('GOOGLE_PUBSUB_TOPIC')

        request = {
            'labelIds': ['INBOX'],
            'topicName': f'projects/{cloud_project}/topics/{pubsub_topic}',
            'labelFilterBehavior': 'INCLUDE'
        }
        return self.api().users().watch(userId='me', body=request).execute()

    def unwatch_mailbox(self):
        return self.api.users().stop(userId='me').execute()
