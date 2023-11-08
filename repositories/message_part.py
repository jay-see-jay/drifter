from typing import List
import mysql.connector

from services.database import Database
from stubs.gmail import GmailMessagePart
from models.user import User


class MessagePartRepo:
    def __init__(self):
        self.db = Database()
        self.byte_limit = 2 ** 16

    def create_many(self, parts: List[GmailMessagePart], user: User):
        if len(parts) == 0:
            return

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

        variables: List[tuple] = []
        for part in parts:  # type: GmailMessagePart
            body_data = part.body.get('data', '')
            base64_bytes = body_data.encode('utf-8')
            byte_count = len(base64_bytes)
            if byte_count >= self.byte_limit:
                body_data = None

            variables.append((
                user.pk,
                part.message_id,
                part.part_id,
                part.mime_type,
                part.filename,
                part.body.get('attachmentId'),
                part.body.get('size'),
                body_data,
                part.parent_part_id,
            ))

        try:
            self.db.insert_many(query, variables)
        except mysql.connector.Error as e:
            print(f'Failed to insert {len(parts)} message parts into db: {e.msg}')
