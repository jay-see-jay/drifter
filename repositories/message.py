from typing import Dict, Set
import mysql.connector
from services import Database
from stubs.gmail import *
from models.user import User


class MessageRepo:
    def __init__(self):
        self.db = Database()

    def create_many(self, messages: List[GmailMessage], user: User):
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
                user.pk,
                message.thread_id,
                message.history_id,
                message.internal_date,
                message.size_estimate,
            ))

        try:
            self.db.insert_many(query, variables)
        except mysql.connector.Error as e:
            print(f'Failed to insert {len(messages)} messages into db: {e.msg}')

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
