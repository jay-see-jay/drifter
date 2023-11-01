from typing import List
import mysql.connector

from services.database import Database
from models.user import User
from stubs.gmail import GmailThread


class ThreadRepo:
    def __init__(self):
        self.db = Database()

    def create_many(self, threads: List[GmailThread], user: User):
        columns = [
            'id',
            'snippet',
            'history_id',
            'user_pk',
        ]

        query = self.db.create_query(columns, 'threads')

        variables: List[tuple] = []
        for thread in threads:  # type: GmailThread
            variables.append((
                thread.thread_id,
                thread.snippet,
                thread.history_id,
                user.pk,
            ))

        try:
            self.db.insert_many(query, variables)
        except mysql.connector.Error as e:
            print(f'Failed to insert {len(threads)} threads into db: {e.msg}')
