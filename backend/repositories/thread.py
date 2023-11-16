from typing import List
import mysql.connector

from services.database import Database
from models.user import User
from stubs.gmail import GmailThread


class ThreadRepo:
    def __init__(
        self,
        user: User
    ):
        self.db = Database()
        self.user = user

    def get_inbox(self) -> List[GmailThread]:
        query = """
            SELECT threads.id FROM threads
            JOIN messages ON messages.thread_id = threads.id
            JOIN messages_labels ON messages_labels.message_id = messages.id
            JOIN labels ON messages_labels.label_pk = labels.pk
            WHERE labels.id = 'INBOX'
            GROUP BY threads.id;
        """

        try:
            response = self.db.query(query, ())
            print(response)
        except mysql.connector.Error as e:
            print(f'Failed to retrieve threads in the inbox: {e}')

    def upsert(self, thread: GmailThread):
        thread_exists = self.exists(thread.thread_id)
        if thread_exists:
            self.update_history_id(thread)
        else:
            self.create_many([thread])

    def update_history_id(self, thread: GmailThread):
        query = 'UPDATE threads SET history_id="%s" WHERE thread_id="%s"'
        variables = (thread.history_id, thread.thread_id)
        try:
            self.db.query(query, variables)
        except mysql.connector.Error as e:
            print(f'Failed to update history_id of thread: {e}')

    def exists(self, thread_id: str) -> bool:
        query = 'SELECT id FROM threads WHERE id="%s"'
        variables = (thread_id,)
        try:
            response = self.db.query(query, variables)
            response_thread_id = response[0].get('id')
            return response_thread_id == thread_id
        except mysql.connector.Error as e:
            if e.msg == 'Not found':
                return False
            print(f'Could not verify that thread was in db: {e}')

    def create_many(self, threads: List[GmailThread]):
        if len(threads) == 0:
            return

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
                self.user.pk,
            ))

        try:
            self.db.insert_many(query, variables)
        except mysql.connector.Error as e:
            print(f'Failed to insert {len(threads)} threads into db: {e.msg}')
