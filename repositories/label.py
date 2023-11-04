from typing import List, TypedDict
import mysql.connector

from services.database import Database
from models.user import User
from stubs.gmail import GmailLabel


class LabelRepo:
    def __init__(self):
        self.db = Database()

    def get(self, user: User):
        query = 'SELECT pk, id FROM labels WHERE user_pk = %s'
        variables = (user.pk,)
        try:
            labels = self.db.query(query, variables)  # type: List[dict]
            label_id_dict = dict()
            for label in labels:
                label_id = label.get('id')
                label_pk = label.get('pk')
                if label_id and label_pk:
                    label_id_dict[label_id] = label_pk

            return label_id_dict
        except mysql.connector.Error as e:
            print(f'Failed to get labels from db: {e.msg}')

    def create_many(self, labels: List[GmailLabel], user: User):
        columns = [
            'id',
            'name',
            'message_list_visibility',
            'label_list_visibility',
            'type',
            'messages_total',
            'messages_unread',
            'threads_total',
            'threads_unread',
            'text_color',
            'background_color',
            'user_pk',
        ]
        query = self.db.create_query(columns, 'labels')
        variables: List[tuple] = []
        for label in labels:  # type: GmailLabel
            variables.append((
                label.label_id,
                label.name,
                label.message_list_visibility,
                label.label_list_visibility,
                label.label_type,
                label.messages_total,
                label.messages_unread,
                label.threads_total,
                label.threads_unread,
                label.color.text_color,
                label.color.background_color,
                user.pk,
            ))

        try:
            self.db.insert_many(query, variables)
        except mysql.connector.Error as e:
            print(f'Failed to insert {len(labels)} labels into db: {e.msg}')
