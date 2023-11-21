from typing import List, Tuple
from datetime import datetime
import mysql.connector
from services import Database
from stubs import History, gmail
from models import User


class HistoryRepo:
    def __init__(self,
                 user: User
                 ):
        self.db = Database()
        self.user = user

    def mark_processed(self, start_history_id: str, history_list: List[History]):
        columns = [
            'id',
            'user_pk',
        ]

        query = self.db.create_update_query(['processed_at'], 'history', columns)
        variables: List[Tuple[datetime, str, int]] = [(datetime.now(), start_history_id, self.user.pk)]

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

    def create_watch(self, response: gmail.WatchSubscriptionResponse):
        columns = [
            'user_pk',
            'history_id',
            'expiration',
        ]

        query = self.db.create_query(columns, 'mailbox_subscriptions')
        history_id = response.get('historyId')
        if not history_id:
            print(f'Failed to add record to mailbox_subscriptions as no history_id was available')
        expiration = response.get('expiration')
        if not expiration:
            print(f'Failed to add record to mailbox_subscriptions as no expiration was available')

        expiration = datetime.fromtimestamp(int(expiration) / 1000.0)

        variables: Tuple[int, str, datetime] = (self.user.pk, history_id, expiration)

        try:
            self.db.insert_one(query, variables)
        except mysql.connector.Error as e:
            print(f'Failed to store the mailbox subscription state: {e.msg}')
