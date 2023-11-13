from typing import List
import mysql.connector

from services.database import Database
from models.user import User
from stubs.gmail import GmailHeader


class HeaderRepo:
    def __init__(self):
        self.db = Database()

    def create_many(self, headers: List[GmailHeader], user: User):
        if len(headers) == 0:
            print('No headers to add')
            return

        required_headers = ['date', 'from', 'sender', 'to', 'cc', 'bcc', 'subject']
        headers = [h for h in headers if h.name.lower() in required_headers]
        columns = [
            'user_pk',
            'message_id',
            'message_part_id',
            'name',
            'value',
        ]
        query = self.db.create_query(columns, 'message_headers')
        variables: List[tuple] = []
        for header in headers:  # type: GmailHeader
            variables.append((
                user.pk,
                header.message_id,
                header.message_part_id,
                header.name,
                header.value,
            ))

        try:
            self.db.insert_many(query, variables)
        except mysql.connector.Error as e:
            print(f'Failed to insert {len(headers)} headers into db: {e.msg}')
