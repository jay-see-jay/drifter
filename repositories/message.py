from typing import List
import mysql.connector
from services.database import Database
from stubs.gmail import GmailMessage
from models.user import User


class MessageRepo:
    def __init__(self):
        self.db = Database()

    def create_many(self, messages: List[GmailMessage], user: User):
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
