import os
import base64
import json
from typing import Dict, Set

from dotenv import load_dotenv
from email.message import EmailMessage
import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from cloudevents.http import CloudEvent

from utilities.general import *
from utilities.user_utils import *
from models.user import User
from repositories import *
from stubs.clerk import OAuthAccessToken
from stubs.gmail import *
from stubs.internal import *

load_dotenv()

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose',
]


class Gmail:
    def __init__(self,
                 auth_user: User,
                 oauth: OAuthAccessToken,
                 ):
        self.user = auth_user
        self.oauth = oauth
        self.user_repo = UserRepo()
        creds = Credentials(
            token=oauth.token,
            token_uri=os.getenv('GOOGLE_TOKEN_URI'),
            client_id=os.getenv('GOOGLE_CLIENT_ID'),
            client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
            scopes=oauth.scopes,
        )

        self.api = build('gmail', 'v1', credentials=creds)
        self.batch = None
        self.batch_request_count = 0
        # Limit set as per https://developers.google.com/gmail/api/guides/batch
        self._batch_request_limit = 50

    def watch_mailbox(self) -> WatchSubscriptionResponse:
        cloud_project = os.getenv('GOOGLE_PROJECT_ID')
        pubsub_topic = os.getenv('GOOGLE_PUBSUB_TOPIC')

        body = {
            'labelIds': ['INBOX'],
            'topicName': f'projects/{cloud_project}/topics/{pubsub_topic}',
            'labelFilterBehavior': 'INCLUDE'
        }
        try:
            return self.api.users().watch(userId='me', body=body).execute()
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
            print(e)
            return []

    def process_history(self, start_history_id: str, history_list: List[History]):
        if len(history_list) == 0:
            return

        history_repo = HistoryRepo(self.user)
        history_repo.create_many(history_list)

        all_message_ids: Dict[str, Set[str]] = dict()  # Message ID, and set of history IDs
        added_message_ids: Dict[str, Set[str]] = dict()
        deleted_message_ids: Dict[str, Set[str]] = dict()
        label_ids: Set[str] = set()

        for history_record in history_list:
            history_id = history_record.get('id')

            all_affected_messages = history_record.get('messages', [])
            for affected_message in all_affected_messages:
                message_id = affected_message['id']
                if message_id not in all_message_ids:
                    all_message_ids[message_id] = set()
                all_message_ids[message_id].add(history_id)

            added_messages = history_record.get('messagesAdded', [])
            for added_message in added_messages:
                msg = added_message['message']
                label_ids.update(msg.get('labelIds', []))

                message_id = msg.get('id')
                if message_id not in added_message_ids:
                    added_message_ids[message_id] = set()
                added_message_ids[message_id].add(history_id)

            deleted_messages = history_record.get('messagesDeleted', [])
            for deleted_message in deleted_messages:
                msg = deleted_message['message']
                label_ids.update(msg.get('labelIds', []))

                message_id = msg.get('id')
                if message_id not in deleted_message_ids:
                    deleted_message_ids[message_id] = set()
                deleted_message_ids[message_id].add(history_id)

            messages_with_labels_added = history_record.get('labelsAdded', [])
            messages_with_labels_removed = history_record.get('labelsRemoved', [])
            for changed_label in messages_with_labels_added + messages_with_labels_removed:
                changed_label_ids = changed_label.get('labelIds', [])
                label_ids.update(changed_label_ids)

        for deleted_message_id in deleted_message_ids:
            if deleted_message_id in all_message_ids:
                del all_message_ids[deleted_message_id]

        message_repo = MessageRepo(self.user)

        existing_message_ids = message_repo.get_by_ids(set(all_message_ids.keys()))

        new_message_ids: Set[str] = set()
        for msg_id in all_message_ids:
            if msg_id not in existing_message_ids:
                new_message_ids.add(msg_id)

        new_messages = self.get_messages_by_ids(new_message_ids)

        thread_ids: Set[str] = set()
        for msg_id in new_messages:
            msg = new_messages[msg_id]
            if msg_id in added_message_ids:
                msg.added_history_id = min(added_message_ids[msg_id])
            thread_ids.add(msg.thread_id)

        threads = self.get_threads_by_ids(thread_ids)

        thread_repo = ThreadRepo(self.user)
        for t_id in threads:
            t = threads[t_id]
            thread_repo.upsert(t)

        messages_list = list(new_messages.values())

        labels = self.get_labels(list(label_ids))
        label_repo = LabelRepo(self.user)
        for lbl in labels:
            label_repo.upsert(lbl)

        existing_labels_dict = label_repo.get_all()
        for history_record in history_list:
            message_repo.process_label_history(existing_labels_dict, history_record)

        message_repo.create_many(messages_list, existing_labels_dict)
        message_repo.delete(deleted_message_ids)
        part_repo = MessagePartRepo()
        header_repo = HeaderRepo()

        headers, message_parts = process_message_parts(messages_list)
        header_repo.create_many(headers, self.user)
        part_repo.create_many(message_parts, self.user)

        message_repo.create_history(all_message_ids)
        history_repo.mark_processed(start_history_id, history_list)

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
        thread_ids = [t.get('id') for t in threads]
        next_page_token = response.get('nextPageToken')
        return {
            'thread_ids': thread_ids,
            'next_page_token': next_page_token
        }

    def get_threads_by_ids(self, thread_ids: Set[str]) -> Dict[str, GmailThread]:
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

    def get_messages_by_ids(self, message_ids: Set[str]) -> Dict[str, GmailMessage]:
        print('messages to get: ', len(message_ids))
        messages: Dict[str, GmailMessage] = dict()

        if len(message_ids) == 0:
            return messages

        def process_message_response(response_id: str, response: dict, exception: HttpError):
            if exception:
                # print(f'{exception.uri}: {exception.reason}')\\
                return
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

    def parse_message_headers(self, part: GmailMessagePart) -> ParsedMessageHeaders:
        # TODO: Try to extract pure email address only
        headers = part.headers
        email_to = ''
        email_from = ''
        subject = ''
        for hdr in headers:
            if hdr['name'] == 'To':
                email_to = check_for_my_email(self.user.email, hdr['value'])
            elif hdr['name'] == 'From':
                email_from = check_for_my_email(self.user.email, hdr['value'])
            elif hdr['name'] == 'Subject':
                subject = hdr['value']

        return ParsedMessageHeaders(
            email_from=email_from,
            email_to=email_to,
            subject=subject
        )

    def parse_message_part(self, part: GmailMessagePart, body: List[str]) -> None:
        if self.is_container_mime_message_part(part):
            child_message_parts = part.parts
            for child_part in child_message_parts:
                self.parse_message_part(child_part, body)
        else:
            message_body = part.body
            mime_type = part.mime_type
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

    def create_draft(self, draft: str, recipient: str, thread_id: str) -> GmailDraft:
        msg = EmailMessage()

        msg.set_content(draft)

        msg['To'] = recipient
        msg['From'] = self.user.email

        # encoded messageg
        encoded_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        create_message = {
            'message': {
                'threadId': thread_id,
                'raw': encoded_message,
            }
        }

        try:
            response = self.api.users().drafts().create(userId="me", body=create_message).execute()
            draft = GmailDraft(
                draft_id=response.get('id'),
                message=response.get('message')
            )
            print(f'Draft id: {draft.draft_id}\nDraft message: {draft.message.snippet}')
            return draft

        except HttpError as e:
            print(f'Failed to create draft in Gmail: {e}')
