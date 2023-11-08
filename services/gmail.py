import os
import base64
import json
from typing import Dict, Set, Tuple

from dotenv import load_dotenv
from email.message import EmailMessage
import google.auth.transport.requests
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from cloudevents.http import CloudEvent

from utilities.general import *
from utilities.user_utils import *
from models.user import User
from repositories import *
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
        self.batch = None
        self.batch_request_count = 0
        # Limit set as per https://developers.google.com/gmail/api/guides/batch
        self._batch_request_limit = 50

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
                creds.refresh(google.auth.transport.requests.Request())
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

    def watch_mailbox(self):
        cloud_project = os.getenv('GOOGLE_PROJECT_ID')
        pubsub_topic = os.getenv('GOOGLE_PUBSUB_TOPIC')

        body = {
            'labelIds': ['INBOX'],
            'topicName': f'projects/{cloud_project}/topics/{pubsub_topic}',
            'labelFilterBehavior': 'INCLUDE'
        }
        try:
            response = self.api.users().watch(userId='me', body=body).execute()
            return response.get('historyId')
        except HttpError as e:
            raise e

    def unwatch_mailbox(self):
        return self.api.users().stop(userId='me').execute()

    @staticmethod
    def decode_cloud_event(cloud_event: CloudEvent) -> SubscriptionMessageData:
        cloud_event_data = base64.b64decode(cloud_event.data['message']['data']).decode()
        cloud_event_data = json.loads(cloud_event_data)

        return {
            'emailAddress': get_value_or_fail(cloud_event_data, 'emailAddress'),
            'historyId': get_value_or_fail(cloud_event_data, 'historyId'),
        }

    def get_history(self, start_history_id: str) -> List[History]:
        history_list: List[History] = []
        try:
            response = self.api.users().history().list(userId='me',
                                                       startHistoryId=start_history_id).execute()
            history_list.extend(response.get('history', []))
            next_page_token = response.get('nextPageToken')
            while next_page_token:
                response = self.api.users().history().list(userId='me',
                                                           startHistoryId=start_history_id,
                                                           pageToken=next_page_token).execute()
                history_list.extend(response.get('history', []))
                next_page_token = response.get('nextPageToken')

            return history_list

        except HttpError as e:
            raise e

    def process_history(self, history_list: List[History]):
        if len(history_list) == 0:
            return

        history_repo = HistoryRepo()
        # TODO : Uncomment
        # history_repo.create_many(history_list, self.user)
        message_history_ids: Dict[str, Set[str]] = dict()
        labels_added_or_removed: Set[str] = set()
        for history_record in history_list:
            history_id = history_record.get('id')
            messages_added = history_record.get('messagesAdded', [])
            messages_with_labels_added = history_record.get('labelsAdded', [])
            messages_with_labels_removed = history_record.get('labelsRemoved', [])
            for changed_label in messages_with_labels_added + messages_with_labels_removed:
                labels_added_or_removed.update(changed_label.get('labelIds', []))

            for message_added in messages_added:
                message_id = message_added['message']['id']
                if message_id not in message_history_ids:
                    message_history_ids[message_id] = set()

                message_history_ids[message_id].add(history_id)

        messages = self.get_messages_by_ids(list(message_history_ids.keys()))

        thread_ids: Set[str] = set()
        for msg_id in messages:
            msg = messages[msg_id]
            msg.added_history_id = message_history_ids[msg_id]
            thread_ids.add(msg.thread_id)

        threads = self.get_threads_by_ids(list(thread_ids))

        thread_repo = ThreadRepo()
        for t_id in threads:
            t = threads[t_id]
            # TODO : Uncomment
            # thread_repo.upsert(t, self.user)

            for msg in t.messages:  # type: GmailMessage
                if msg.message_id not in message_history_ids:
                    messages[msg.message_id] = msg

        message_ids_to_delete: List[Tuple[str, str]] = []
        for history_record in history_list:
            history_id = history_record.get('id')
            messages_deleted = history_record.get('messagesDeleted', [])
            for messages_deleted in messages_deleted:
                message_id = messages_deleted['message']['id']
                if message_id not in message_history_ids:
                    message_history_ids[message_id] = set()

                message_history_ids[message_id].add(history_id)

                if message_id in messages:
                    messages[message_id].deleted_history_id = history_id
                else:
                    message_ids_to_delete.append((message_id, history_id))

        messages_list = list(messages.values())
        message_repo = MessageRepo(self.user)
        # TODO : Uncomment
        # message_repo.create_many(messages_list)
        # message_repo.mark_deleted(message_ids_to_delete)
        part_repo = MessagePartRepo()
        header_repo = HeaderRepo()

        headers, message_parts = process_message_parts(messages_list)
        # TODO : Uncomment
        # header_repo.create_many(headers, self.user)
        # TODO : Uncomment
        # part_repo.create_many(message_parts, self.user)

        label_messages = create_label_messages_dict(messages_list)
        labels_added_or_removed.update(label_messages.keys())
        labels = self.get_labels(list(labels_added_or_removed))
        label_repo = LabelRepo(self.user)
        # TODO : Uncomment
        # for lbl in labels:
        #   label_repo.upsert(lbl)
        # TODO: Update messages_labels
        # TODO : Ensure all the labels in labels_added and labels_removed are in the db
        existing_labels_dict = label_repo.get_all()
        for history_record in history_list:
            message_repo.process_label_history(existing_labels_dict, history_record, 'added')
            message_repo.process_label_history(existing_labels_dict, history_record, 'removed')

        # TODO : Uncomment
        # message_repo.create_history(message_history_ids)
        # TODO : Finish by updating `processed_at` column

    def create_batch(self, callback):
        if self.batch is not None or self.batch_request_count != 0:
            print('Please finalise previous batch request before creating a new one')
            return

        self.batch = self.api.new_batch_http_request(callback)

    def add_to_batch(self, request):
        self.batch.add(request)
        self.batch_request_count += 1
        if self.batch_request_count >= self._batch_request_limit:
            self.batch.execute()
            self.batch_request_count = 0

    def finalise_batch(self):
        self.batch.execute()
        self.batch_request_count = 0
        self.batch = None

    def get_thread(self, thread_id: str) -> GmailThread:
        try:
            response = self.api.users().threads().get(userId='me', id=thread_id).execute()
            return GmailThread(
                thread_id=response.get('id'),
                history_id=response.get('historyId'),
                messages=response.get('messages'),
                snippet=response.get('snippet'),
            )

        except HttpError as e:
            print(f'Failed to get thread from Gmail: {e}')

    def get_threads(self, page_token=None, count=50) -> GmailThreadsListResponse:
        response = self.api.users().threads().list(userId='me', pageToken=page_token, maxResults=count).execute()
        threads = response.get('threads', [])
        thread_ids = [thread.get('id') for thread in threads]
        next_page_token = response.get('nextPageToken')
        return {
            'thread_ids': thread_ids,
            'next_page_token': next_page_token
        }

    def get_threads_by_ids(self, thread_ids: List[str]) -> Dict[str, GmailThread]:
        threads: Dict[str, GmailThread] = dict()

        if len(thread_ids) == 0:
            return threads

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

        self.create_batch(process_thread_response)
        for thread_id in thread_ids:
            request = self.api.users().threads().get(userId='me', id=thread_id)
            self.add_to_batch(request)

        self.finalise_batch()

        return threads

    def get_messages_by_ids(self, message_ids: List[str]) -> Dict[str, GmailMessage]:
        messages: Dict[str, GmailMessage] = dict()

        if len(message_ids) == 0:
            return messages

        def process_message_response(response_id: str, response: dict, exception):
            if exception is not None:
                print(f'Response ID: {response_id} - failed to get message.\n{exception}')
            else:
                msg_id = response.get('id')
                messages[msg_id] = GmailMessage(
                    message_id=msg_id,
                    thread_id=response.get('threadId'),
                    label_ids=response.get('labelIds'),
                    snippet=response.get('snippet'),
                    history_id=response.get('historyId'),
                    internal_date=response.get('internalDate'),
                    payload=response.get('payload'),
                    size_estimate=response.get('sizeEstimate'),
                )

        self.create_batch(process_message_response)
        for message_id in message_ids:
            request = self.api.users().messages().get(userId='me', id=message_id)
            self.add_to_batch(request)

        self.finalise_batch()

        return messages

    def get_message_by_id(self, message_id: str) -> GmailMessage:
        try:
            response = self.api.users().messages().get(userId='me', id=message_id).execute()
            return GmailMessage(
                message_id=response.get('id'),
                thread_id=response.get('threadId'),
                label_ids=response.get('labelIds'),
                snippet=response.get('snippet'),
                history_id=response.get('historyId'),
                internal_date=response.get('internalDate'),
                payload=response.get('payload'),
                size_estimate=response.get('sizeEstimate'),
            )
        except HttpError as e:
            print(f'Failed to get message from Gmail: {e}')

    def get_labels(self, label_ids: List[str]) -> List[GmailLabel]:
        labels: List[GmailLabel] = []

        if len(label_ids) == 0:
            return labels

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

        self.create_batch(process_label_response)
        for label_id in label_ids:
            request = self.api.users().labels().get(userId='me', id=label_id)
            self.add_to_batch(request)

        self.finalise_batch()

        return labels

    @staticmethod
    def parse_message_headers(message_part: GmailMessagePart) -> ParsedMessageHeaders:
        # TODO: Try to extract pure email address only
        headers = message_part.headers
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
            child_message_parts = message_part.parts
            for child_part in child_message_parts:
                self.parse_message_part(child_part, body)
        else:
            message_body = message_part.body
            mime_type = message_part.mime_type
            if self.body_has_data(message_body) and mime_type == 'text/plain':
                decoded_data = self.decode_body(message_body)
                body.append(decoded_data)

    @staticmethod
    def body_has_data(body: GmailMessagePartBody) -> bool:
        return body and body['size'] > 0

    @staticmethod
    def is_container_mime_message_part(payload: GmailMessagePart) -> bool:
        mime_type = payload.mime_type
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

        # encoded messageg
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
