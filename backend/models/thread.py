from typing import List, Tuple, Set, Dict
import mysql.connector
from models import Message, User, MessageCreateVariablesType
from services import Database
from stubs import GmailLabel, LabelCreateVariablesType, LabelUpdateVariablesType, MessagePartCreateVariablesType


class Thread:
    def __init__(
        self,
        user: User,
        thread_id: str,
        snippet: str,
        history_id: str,
        messages: List[Message],
    ):
        self.user = user
        self.db = Database()
        self.create_columns = [
            'id',
            'snippet',
            'history_id',
            'user_pk',
        ]
        self.thread_id = thread_id
        self.snippet = snippet
        self.history_id = history_id
        self.messages = messages
        self.label_ids = None
        self.labels: Dict[str, GmailLabel] = dict()

    def get_all_label_ids(self) -> Set[str]:
        label_ids = set()
        for msg in self.messages:
            if not msg.label_ids:
                continue
            label_ids.update(msg.label_ids)
        return label_ids

    def get_existing_messages(self) -> List[str]:
        query = 'SELECT id FROM messages WHERE thread_id=%s'
        existing_messages = self.db.query(query, (self.thread_id,))
        return [msg.get('id') for msg in existing_messages]

    def get_existing_labels(self) -> Dict[str, int]:
        query = 'SELECT id, pk FROM labels WHERE user_pk=%s'
        existing_labels = self.db.query(query, (self.user.pk,))
        labels_id_pk: Dict[str, int] = dict()
        for label in existing_labels:
            labels_id_pk[label.get('id')] = label.get('pk')
        return labels_id_pk

    def separate_new_messages(self) -> Tuple[List[Message], List[Message]]:
        existing_message_ids = self.get_existing_messages()
        new_messages: List[Message] = []
        existing_messages: List[Message] = []
        for message in self.messages:
            if message.message_id in existing_message_ids:
                existing_messages.append(message)
            else:
                new_messages.append(message)

        return new_messages, existing_messages

    def separate_new_labels(self) -> Tuple[List[GmailLabel], List[GmailLabel]]:
        existing_label_ids = self.get_existing_labels()
        existing_label_ids = list(existing_label_ids.keys())
        new_labels: List[GmailLabel] = []
        existing_labels: List[GmailLabel] = []
        for label_id in self.labels:
            if label_id in existing_label_ids:
                existing_labels.append(self.labels[label_id])
            else:
                new_labels.append(self.labels[label_id])

        return new_labels, existing_labels

    def in_database(self) -> bool:
        query = 'SELECT id FROM threads WHERE id=%s'
        variables = (self.thread_id,)
        try:
            response = self.db.query(query, variables)
            response_thread_id = response[0].get('id')
            return response_thread_id == self.thread_id
        except mysql.connector.Error as e:
            if e.msg == 'Not found':
                return False
            print(f'Could not verify that thread was in db: {e}')

    def store(self):
        try:
            thread_exists = self.in_database()
            new_messages, existing_messages = self.separate_new_messages()
            new_labels, existing_labels = self.separate_new_labels()
            if thread_exists:
                self.update_thread()
            else:
                self.insert_thread()
            self.insert_labels(new_labels)
            self.update_labels(existing_labels)
            existing_label_id_pks = self.get_existing_labels()
            self.db.connection.autocommit = False
            for label_id in self.labels:
                self.labels[label_id].pk = existing_label_id_pks[label_id]
            self.insert_messages(new_messages)
            self.update_messages(existing_messages)
            self.db.connection.commit()
        except mysql.connector.Error as e:
            print(f'Failed to store thread: {e}')

    def insert_thread(self):
        query = self.db.create_query(self.create_columns, 'threads')
        variables: Tuple[str, str, str, int] = (
            self.thread_id,
            self.snippet,
            self.history_id,
            self.user.pk,
        )
        self.db.insert_one(query, variables)

    def update_thread(self):
        query = 'UPDATE threads SET history_id=%s WHERE id=%s'
        variables = (self.history_id, self.thread_id)
        self.db.insert_one(query, variables)

    def insert_messages(self, messages: List[Message] = None):
        if len(messages) == 0:
            return

        query = self.db.create_query(messages[0].create_columns, 'messages')
        variables: List[MessageCreateVariablesType] = [
            (
                msg.message_id,
                msg.snippet,
                self.user.pk,
                self.thread_id,
                msg.history_id,
                msg.internal_date,
                msg.added_history_id,
                msg.size_estimate,
            )
            for msg in messages
        ]
        self.db.insert_many(query, variables)
        self.insert_message_parts(messages)
        self.insert_messages_labels(messages)

    def insert_message_parts(self, messages: List[Message]):
        columns = [
            'user_pk',
            'message_id',
            'part_id',
            'mime_type',
            'filename',
            'body_attachment_id',
            'body_size',
            'body_data',
            'parent_message_part_id',
        ]
        query = self.db.create_query(columns, 'message_parts')
        part_variables: List[tuple] = []
        header_variables: List[tuple] = []
        for message in messages:
            for part in message.parts:
                part_variables.append((
                    self.user.pk,
                    message.message_id,
                    part.part_id,
                    part.mime_type,
                    part.filename,
                    part.body.attachment_id,
                    part.body.size,
                    part.body.data,
                    part.get_parent_part_id(),
                ))
                for header in part.headers:
                    header_variables.append((
                        self.user.pk,
                        message.message_id,
                        part.part_id,
                        header.name,
                        header.value,
                    ))
        self.db.insert_many(query, part_variables)
        self.insert_message_headers(header_variables)

    def insert_message_headers(self, variables: List[tuple]):
        header_columns = [
            'user_pk',
            'message_id',
            'message_part_id',
            'name',
            'value',
        ]
        query = self.db.create_query(header_columns, 'message_headers')
        self.db.insert_many(query, variables)

    def insert_messages_labels(self, messages: List[Message]):
        columns = ['label_pk', 'message_id']
        query = self.db.create_query(columns, 'messages_labels')
        variables: List[Tuple[int, str]] = []
        for message in messages:
            for label_id in message.label_ids:
                variables.append((
                    self.labels[label_id].pk,
                    message.message_id,
                ))
        self.db.insert_many(query, variables)

    def update_messages(self, existing_messages: List[Message]):
        query = 'UPDATE messages SET history_id=%s WHERE id=%s'
        variables: List[Tuple[str, str]] = []
        for message in existing_messages:
            variables.append((
                message.history_id,
                message.message_id,
            ))
        self.db.insert_many(query, variables)

        self.update_messages_labels(existing_messages)

    def update_messages_labels(self, existing_messages: List[Message]):
        current_message_labels = self.get_messages_current_labels(existing_messages)
        added_message_labels: Dict[str, Set[int]] = dict()
        removed_message_labels: Dict[str, Set[int]] = dict()

        for message in existing_messages:
            current_labels = current_message_labels.get(message.message_id)
            if not current_labels:
                continue

            for label in message.label_ids:
                if label not in current_labels:
                    label_pk = self.labels.get(label).pk
                    added_message_labels.setdefault(message.message_id, set()).add(label_pk)

            for label in current_labels:
                if label not in message.label_ids:
                    label_pk = self.labels.get(label).pk
                    removed_message_labels.setdefault(message.message_id, set()).add(label_pk)

        self.add_messages_labels(added_message_labels)
        self.remove_messages_labels(removed_message_labels)

    def add_messages_labels(self, message_labels: Dict[str, Set[int]]):
        if len(message_labels) == 0:
            return

        columns = ['label_pk', 'message_id']
        query = self.db.create_query(columns, 'messages_labels')
        print('add query', query)
        variables = []

        for message_id in message_labels:
            labels = message_labels[message_id]
            for label_pk in labels:
                variables.append((
                    label_pk,
                    message_id
                ))

        self.db.insert_many(query, variables)

    def remove_messages_labels(self, message_labels: Dict[str, Set[int]]):
        if len(message_labels) == 0:
            return

        columns = ['label_pk', 'message_id']
        query = self.db.create_delete_query(columns, 'messages_labels')
        print('remove query', query)
        variables = []

        for message_id in message_labels:
            labels = message_labels[message_id]
            for label_pk in labels:
                variables.append((
                    label_pk,
                    message_id
                ))

        self.db.insert_many(query, variables)

    def get_messages_current_labels(self, messages: List[Message]) -> Dict[str, Set[str]]:
        format_strings = ','.join(['%s'] * len(messages))
        query = """
            SELECT
                messages_labels.message_id,
                GROUP_CONCAT(labels.id) AS labels
            FROM
                messages_labels
            JOIN
                labels ON messages_labels.label_pk = labels.pk
            WHERE
                messages_labels.message_id IN (%s)
            GROUP BY
                messages_labels.message_id;
        """ % format_strings

        variables = tuple([message.message_id for message in messages])

        response = self.db.query(query, variables)

        result: Dict[str, Set[str]] = dict()

        for row in response:
            message_id = row.get('message_id')
            message_labels = row.get('labels')
            message_labels = set(message_labels.split(',') if message_labels else [])
            result[message_id] = message_labels

        return result

    def insert_labels(self, labels: List[GmailLabel]):
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

        variables: List[LabelCreateVariablesType] = [
            (
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
            )
            for label in labels
        ]

        self.db.insert_many(query, variables)

    def update_labels(self, labels: List[GmailLabel]):
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

        filter_columns = ['id', 'user_pk']

        query = self.db.create_update_query(columns, 'labels', filter_columns)
        variables: List[LabelUpdateVariablesType] = [
            (
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
                label.label_id,
                self.user.pk

            )
            for label in labels
        ]

        self.db.insert_many(query, variables)
