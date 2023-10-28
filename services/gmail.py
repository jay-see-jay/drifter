import os
import base64
import json

from dotenv import load_dotenv
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from cloudevents.http import CloudEvent

from utilities.dict_utils import get_value_or_fail
from utilities.email_utils import *
from models.user import User
from repositories.user import UserRepo
from stubs.gmail import *
from stubs.internal import *

load_dotenv()

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose',
]


class Gmail:
    def __init__(self,
                 user: User
                 ):
        self.user = user
        self.user_repo = UserRepo()
        token_dict = self._get_user_auth(user)
        creds = Credentials.from_authorized_user_info(token_dict, SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            success = self._refresh_credentials(creds)
            if not success:
                creds = self._request_authorization()

        self.api = build('gmail', 'v1', credentials=creds)

    @staticmethod
    def _get_user_auth(user: User) -> dict:
        return {
            'token': user.access_token,
            'refresh_token': user.refresh_token,
            'token_uri': os.getenv('GOOGLE_TOKEN_URI'),
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'scopes': SCOPES,
            'expiry': os.getenv('TEMP_TOKEN_EXPIRY')
        }

    @staticmethod
    def _get_credentials() -> dict:
        return {
            'web': {
                'client_id': os.getenv('GOOGLE_CLIENT_ID'),
                'project_id': os.getenv('GOOGLE_PROJECT_ID'),
                'auth_uri': os.getenv('GOOGLE_AUTH_URI'),
                'token_uri': os.getenv('GOOGLE_TOKEN_URI'),
                'auth_provider_x509_cert_url': os.getenv('GOOGLE_AUTH_PROVIDER'),
                'client_secret': os.getenv('GOOGLE_CLIENT_SECRET')
            }
        }

    def _refresh_credentials(self, creds: Credentials, ) -> bool:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                return True
            except RefreshError as e:
                error_description = e.args[1].get('error_description')
                print(f'Could not refresh credentials: {error_description}')
                print('Deleting user credentials')
                self.user_repo.remove_credentials(user=self.user)

        return False

    def _request_authorization(self) -> Credentials:
        creds_dict = self._get_credentials()
        flow = InstalledAppFlow.from_client_config(
            creds_dict, SCOPES)

        creds = flow.run_local_server(approval_prompt='force')
        print('Saving new credentials')
        self.user_repo.save_credentials(user=self.user, creds=creds)
        return creds

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

    def get_threads(self, next_page_token=None, count=50) -> GmailThreadsListResponse:
        return self.api.users().threads().list(userId='me', pageToken=next_page_token, maxResults=count).execute()

    @staticmethod
    def decode_cloud_event(cloud_event: CloudEvent) -> SubscriptionMessageData:
        cloud_event_data = base64.b64decode(cloud_event.data['message']['data']).decode()
        cloud_event_data = json.loads(cloud_event_data)

        return {
            'emailAddress': get_value_or_fail(cloud_event_data, 'emailAddress'),
            'historyId': get_value_or_fail(cloud_event_data, 'historyId'),
        }

    def get_changed_thread_ids(self, start_history_id='125125') -> set[str]:
        try:
            response = self.api.users() \
                .history().list(userId='me', startHistoryId=start_history_id).execute()  # type: HistoryResponse
            # TODO: Update latest historyId in database: response['historyId']
            # TODO: Get next page if there is a nextPageToken: response['nextPageToken']
            history_list = response.get('history')

            messages: List[GmailMessageTruncated] = []

            if history_list:
                for item in history_list:
                    item_messages = item.get('messages', [])
                    messages.extend(item_messages)

            affected_thread_ids: set[str] = set()

            for message in messages:
                affected_thread_ids.add(message['threadId'])

            return affected_thread_ids

        except HttpError as e:
            print(f'Failed to get history of mailbox changes: {e}')

    def get_threads_by_ids(self, thread_ids: List[str], callback):
        batch = self.api.new_batch_http_request(callback)
        for thread_id in thread_ids:
            request = self.api.users().threads().get(userId='me', id=thread_id)
            batch.add(request)
        batch.execute()

    def get_thread_by_id(self, thread_id: str) -> GmailThread:
        try:
            return self.api.users().threads().get(userId='me', id=thread_id).execute()

        except HttpError as e:
            print(f'Failed to get thread from Gmail: {e}')

    @staticmethod
    def parse_message_headers(message_part: GmailMessagePart) -> ParsedMessageHeaders:
        # TODO: Try to extract pure email address only
        headers = message_part['headers']
        email_to = ''
        email_from = ''
        subject = ''
        for header in headers:
            if header['name'] == 'To':
                email_to = check_for_my_email(header['value'])
            elif header['name'] == 'From':
                email_from = check_for_my_email(header['value'])
            elif header['name'] == 'Subject':
                subject = header['value']

        return ParsedMessageHeaders(
            email_from=email_from,
            email_to=email_to,
            subject=subject
        )

    def parse_message_part(self, message_part: GmailMessagePart, body: List[str]) -> None:
        if self.is_container_mime_message_part(message_part):
            child_message_parts = message_part['parts']
            for child_part in child_message_parts:
                self.parse_message_part(child_part, body)
        else:
            message_body = message_part['body']
            mime_type = message_part['mimeType']
            if self.body_has_data(message_body) and mime_type == 'text/plain':
                decoded_data = self.decode_body(message_body)
                body.append(decoded_data)

    @staticmethod
    def body_has_data(body: GmailMessagePartBody) -> bool:
        return body and body['size'] > 0

    @staticmethod
    def is_container_mime_message_part(payload: GmailMessagePart) -> bool:
        mime_type = payload['mimeType']
        return mime_type and mime_type.startswith('multipart/')

    @staticmethod
    def decode_bytes(data: bytes) -> str:
        try:
            return base64.urlsafe_b64decode(data).decode('utf-8')
        except Exception as e:
            print(f'An error occurred while decoding: {e}')

    def decode_body(self, body: GmailMessagePartBody) -> str:
        return self.decode_bytes(body['data'])

    @staticmethod
    def create_draft(draft: str, recipient: str, thread_id: str):
        message = EmailMessage()

        message.set_content(draft)

        message['To'] = recipient
        message['From'] = get_my_email()

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {
            'message': {
                'threadId': thread_id,
                'raw': encoded_message,
            }
        }

        try:
            # draft = self.api().users().drafts().create(userId="me", body=create_message).execute()
            # print(f'Draft id: {draft["id"]}\nDraft message: {draft["message"]}')\
            print('Adding draft to Gmail disabled for now.')

        except HttpError as e:
            print(f'Failed to create draft in Gmail: {e}')
