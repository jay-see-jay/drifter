import mysql.connector
from datetime import datetime
from typing import Optional, List, Tuple
from services import Database
from stubs.internal import DatabaseError


class Draft:
    def __init__(
        self,
        database: Database,
        draft_id: str,
        message_id: str,
        thread_id: str,
        label_ids: Optional[List[str]] = None,
        created_at: Optional[datetime] = None,
    ):
        self.db = database
        self.create_columns = [
            'id',
            'message_id',
            'thread_id',
            'user_pk'
        ]
        self.draft_id = draft_id
        self.created_at = created_at
        self.message_id = message_id
        self.thread_id = thread_id
        self.label_ids = label_ids

    def store(self, user_pk: int):
        query = self.db.create_query(self.create_columns, 'drafts')
        variables: Tuple[str, str, str, int] = (
            self.draft_id,
            self.message_id,
            self.thread_id,
            user_pk,
        )

        try:
            self.db.insert_one(query, variables)
            return self.db.cursor.lastrowid
        except mysql.connector.Error as e:
            raise DatabaseError(f'Error creating draft in database: {e}')
