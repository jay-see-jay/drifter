from typing import Dict, Set, Tuple
import mysql.connector
from services import Database
from stubs.gmail import *
from models.user import User


class MessageRepo:
    def __init__(self, user: User):
        self.db = Database()
        self.user = user

    def create_many(self, messages: List[GmailMessage]):
        if len(messages) == 0:
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
