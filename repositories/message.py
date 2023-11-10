from typing import Dict, Set, Tuple, Optional
import mysql.connector
from services import Database
from stubs.gmail import *
from models.user import User

MessageLabelHistoryAction = Literal['added', 'removed']


class MessageRepo:
    def __init__(self, user: User):
        self.db = Database()
        self.user = user

    def get(self, message_id: str) -> Optional[GmailMessage]:
        query = 'SELECT * FROM messages WHERE id=%s'
        variables = (message_id,)

        try:
            response = self.db.query(query, variables)
            result = response[0]
            return GmailMessage(
                message_id=result.get('id'),
                thread_id=result.get('thread_id'),
                label_ids=[],
                snippet=result.get('snippet'),
                history_id=result.get('history_id'),
                internal_date=result.get('internal_date'),
                payload=result.get('payload'),
                size_estimate=result.get('size_estimate'),
                added_history_id=result.get('added_history_id'),
                deleted_history_id=result.get('deleted_history_id'),
            )
        except mysql.connector.Error as e:
            if e.msg == 'Not found':
                return None
            else:
                print(f'Failed to get message from db: {e}')

    def create_many(self, messages: List[GmailMessage]):
        if len(messages) == 0:
            print('No new messages to create')
            return

        columns = [
            'id',
            'snippet',
            'user_pk',
            'thread_id',
            'history_id',
            'internal_date',
            'size_estimate',
        ]

        query = self.db.create_query(columns, 'messages')

        variables: List[tuple] = []
        for message in messages:  # type: GmailMessage
            variables.append((
                message.message_id,
                message.snippet,
                self.user.pk,
                message.thread_id,
                message.history_id,
                message.internal_date,
                message.size_estimate,
            ))

        try:
            self.db.insert_many(query, variables)
        except mysql.connector.Error as e:
            print(f'Failed to insert {len(messages)} messages into db: {e.msg}')

    def create_history(self, message_history_ids: Dict[str, Set[str]]):
        if len(message_history_ids) == 0:
            print('No messages history to update')
            return

        columns = [
            'message_id',
            'history_id',
        ]

        query = self.db.create_query(columns, 'messages_history')

        variables: List[Tuple[str, str]] = []

        for message_id in message_history_ids:
            history_ids = message_history_ids[message_id]
            for history_id in history_ids:
                variables.append((message_id, history_id))

        try:
            self.db.insert_many(query, variables)
        except mysql.connector.Error as e:
            print(f'Failed to insert history for {len(message_history_ids)} into db: {e.msg}')

    def store_labels(
        self,
        label_messages: Dict[str, Set[str]],
        label_pks: Dict[str, int],
    ):
        variables: List[tuple] = []
        for label_id in label_messages:  # type: str
            label_pk = label_pks.get(label_id)
            if not label_pk:
                continue
            messages = label_messages[label_id]  # type: Set[str]

            for message_id in messages:
                variables.append((label_pk, message_id))

        columns = ['label_pk', 'message_id']

        query = self.db.create_query(columns, 'messages_labels')

        try:
            self.db.insert_many(query, variables)
        except mysql.connector.Error as e:
            print(f'Failed to create relations between messages and {len(label_messages)} labels: {e.msg}')

    def process_label_history(self,
                              label_pk_dict: Dict[str, int],
                              history_record: History,
                              ):

        history_id = history_record['id']

        labels_added = history_record.get('labelsAdded', [])
        labels_removed = history_record.get('labelsRemoved', [])

        self.edit_labels(label_pk_dict, labels_added, 'added', history_id)
        self.edit_labels(label_pk_dict, labels_removed, 'removed', history_id)

    def edit_labels(
        self,
        label_pk_dict: Dict[str, int],
        label_messages: List[HistoryLabelsChanged],
        action: MessageLabelHistoryAction,
        history_id: str = None,
    ):
        if not (action == 'added' or action == 'removed'):
            raise Exception('Action must be one of "added" or "removed"')

        variables: List[Tuple[int, str]] = []

        for label_message in label_messages:
            label_ids = label_message.get('labelIds', [])
            message_id = label_message['message']['id']
            message_labels = [(label_pk_dict[label_id], message_id) for label_id in label_ids]
            variables.extend(message_labels)

        if len(variables) == 0:
            return

        columns = ['label_pk', 'message_id']
        query: str
        if action == 'added':
            query = self.db.create_query(columns, 'messages_labels')
        else:
            query = self.db.create_delete_query(columns, 'messages_labels')

        try:
            self.db.insert_many(query, variables)
        except mysql.connector.Error as e:
            print(f'Failed to edit labels (action: {action}): {e}')

        if history_id:
            self.store_messages_labels_history(variables, history_id, action)

    def store_messages_labels_history(
        self,
        label_pk_messages: List[Tuple[int, str]],
        history_id: str,
        action: MessageLabelHistoryAction,
    ):
        columns = ['label_pk', 'message_id', 'history_id', 'action']
        query = self.db.create_query(columns, 'messages_labels_history')
        variables: List[Tuple[int, str, str, MessageLabelHistoryAction]] = []

        for label_pk_message in label_pk_messages:
            variables.append(label_pk_message + (history_id, action))

        try:
            self.db.insert_many(query, variables)
        except mysql.connector.Error as e:
            print(f'Failed to add history record of change to message labels: {e}')

    def delete(self, message_history_ids: Dict[str, Set[str]]):
        if len(message_history_ids) == 0:
            print('No messages to delete')
            return

        tables = [
            'message_headers',
            'message_parts',
            'messages_history',
            'messages_labels',
            'messages_labels_history',
        ]

        queries = [
            self.db.create_delete_query(['id'], 'messages'),
        ]

        for table in tables:
            query = self.db.create_delete_query(['message_id'], table)
            queries.append(query)

        variables: List[Tuple[str]] = []

        for message_id in message_history_ids:
            message = self.get(message_id)
            if message:
                variables.append((message_id,))

        for query in queries:
            try:
                self.db.insert_many(query, variables)
            except mysql.connector.Error as e:
                print(f'Failed to execute query: {query}\n{e.msg}')
