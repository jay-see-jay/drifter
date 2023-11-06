from typing import List
import mysql.connector
from services import Database
from stubs import History
from models import User


class HistoryRepo:
    def __init__(self):
        self.db = Database()

    def create_many(self, history_list: List[History], user: User):
        columns = [
            'id',
            'user_pk',
        ]

        query = self.db.create_query(columns, 'history')
        variables: List[tuple] = []
        for history in history_list:  # type: History
            variables.append((
                history.get('id'),
                user.pk,
            ))

        try:
            self.db.insert_many(query, variables)
        except mysql.connector.Error as e:
            print(f'Failed to insert {len(history_list)} changes to history into db: {e.msg}')
