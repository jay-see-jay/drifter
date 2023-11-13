from typing import List, Optional, Dict, Set
import mysql.connector

from services.database import Database
from models.user import User
from stubs.gmail import GmailLabel


class LabelRepo:
    def __init__(self, user: User):
        self.db = Database()
        self.user = user

    @staticmethod
    def instantiate_label(row: dict) -> GmailLabel:
        return GmailLabel(
            label_id=row.get('id'),
            name=row.get('name'),
            label_type=row.get('type'),
            message_list_visibility=row.get('message_list_visibility'),
            label_list_visibility=row.get('label_list_visibility'),
            messages_total=row.get('messages_total'),
            messages_unread=row.get('messages_unread'),
            threads_total=row.get('threads_total'),
            threads_unread=row.get('threads_unread'),
            color={
                'text_color': row.get('text_color'),
                'background_color': row.get('background_color')
            },
        )

    def get(self, label: GmailLabel) -> Optional[GmailLabel]:
        query = 'SELECT * FROM labels WHERE id=%s AND user_pk=%s LIMIT 1'
        variables = (label.label_id, self.user.pk)
        try:
            response = self.db.query(query, variables)
            return self.instantiate_label(response[0])
        except mysql.connector.Error as e:
            if e.msg == 'Not found':
                return None
            print(f'Could not retrieve label from db: {e}')

    def get_all(self) -> Dict[str, int]:
        query = 'SELECT pk, id FROM labels WHERE user_pk = %s'
        variables = (self.user.pk,)
        try:
            labels = self.db.query(query, variables)  # type: List[dict]
            label_id_dict: Dict[str, int] = dict()
            for label in labels:
                label_id = label.get('id')
                label_pk = label.get('pk')
                if label_id and label_pk:
                    label_id_dict[label_id] = label_pk

            return label_id_dict
        except mysql.connector.Error as e:
            print(f'Failed to get labels from db: {e.msg}')

    def upsert(self, label: GmailLabel):
        existing_label = self.get(label)
        if existing_label:
            print(f'Update existing label: {label.label_id}')
            self.update(existing_label, label)
        else:
            print(f'Create new label: {label.label_id}')
            self.create_many([label])

    def update(self, existing: GmailLabel, updated: GmailLabel):
        columns = [
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
        ]

        updated_dict = updated.__dict__
        changed_columns = self.db.filter_changed_columns(existing.__dict__, updated_dict, columns)
        changed_variables = []

        for col in changed_columns:
            changed_variables.append(updated_dict[col])

        filter_columns = ['id', 'user_pk']
        filter_variables = (updated.label_id, self.user.pk)

        query = self.db.create_update_query(changed_columns, 'labels', filter_columns)

        try:
            self.db.insert_one(query, tuple(changed_variables) + filter_variables)
        except mysql.connector.Error as e:
            print(f'Failed to update label: {e}')
            print('query', query)

    def create_many(self, labels: List[GmailLabel]):
        if len(labels) == 0:
            return

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
                self.user.pk,
            ))

        try:
            self.db.insert_many(query, variables)
        except mysql.connector.Error as e:
            print(f'Failed to insert {len(labels)} labels into db: {e.msg}')
