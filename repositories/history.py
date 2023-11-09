from typing import List, Tuple
from datetime import datetime
import mysql.connector
from services import Database
from stubs import History
from models import User


class HistoryRepo:
    def __init__(self,
                 user: User
                 ):
        self.db = Database()
        self.user = user

    def mark_processed(self, history_list: List[History]):
        columns = [
            'id',
            'user_pk',
        ]

        query = self.db.create_update_query(['created_at'], 'history', columns)
        variables: List[Tuple[datetime, str, int]] = []

        for history in history_list:
            history_id = history['id']
            variables.append((datetime.now(), history_id, self.user.pk))

        try:
            self.db.insert_many(query, variables)
        except mysql.connector.Error as e:
            print(f'Failed to mark {len(history_list)} history records as processed: {e}')

    def create_many(self, history_list: List[History]):
        columns = [
            'id',
            'user_pk',
        ]

        query = self.db.create_query(columns, 'history')
        variables: List[tuple] = []
        for history in history_list:  # type: History
            variables.append((
                history.get('id'),
                self.user.pk,
            ))

        try:
            self.db.insert_many(query, variables)
        except mysql.connector.Error as e:
            print(f'Failed to insert {len(history_list)} changes to history into db: {e.msg}')
