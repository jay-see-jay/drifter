import mysql.connector
from dotenv import load_dotenv
from flask import Request
from werkzeug.exceptions import HTTPException
from typing import List, Tuple, Optional

from services.database import Database
from utilities.user_utils import get_user_id_from_path
from models.user import User

load_dotenv()


class UserRepo:
    def __init__(self):
        self.db = Database()
        self.create_columns = [
            'email',
            'clerk_user_id',
            'is_active',
        ]
        self.all_columns = self.create_columns + [
            'pk',
            'created_at',
        ]

    def create_user(self, new_user: User) -> Optional[int]:
        query = f'INSERT INTO users ({", ".join(self.create_columns)}) VALUES (%s, %s, %s)'

        variables: Tuple[str, str, bool] = (
            new_user.email,
            new_user.clerk_user_id,
            new_user.is_active,
        )

        self.db.insert_one(query, variables)

        return self.db.cursor.lastrowid

        self.db.close()

    def get_all_users(self) -> List[User]:
        query = f'SELECT {", ".join(self.all_columns)} FROM users'
        try:
            response = self.db.query(query, ())
            users: List[User] = []
            for row in response:
                users.append(User(
                    pk=row.get('pk'),
                    email=row.get('email'),
                    is_active=row.get('is_active'),
                    clerk_user_id=row.get('clerk_user_id')
                ))
            return users
        except mysql.connector.Error as e:
            e.msg = 'Failed to get all users'
            raise e

    def _get_user(self, query, variables) -> User:
        try:
            response = self.db.query(query, variables)
        except mysql.connector.Error as e:
            e.msg = 'User not found'
            raise e

        return User(
            pk=response[0].get('pk'),
            email=response[0].get('email'),
            is_active=response[0].get('is_active'),
            clerk_user_id=response[0].get('clerk_user_id')
        )

    def get_user_from_request(self, request: Request) -> User:
        user_id = get_user_id_from_path(request)
        if not user_id:
            raise HTTPException('User ID not found in request')

        try:
            return self.get_user_by_id(user_id)
        except mysql.connector.Error as e:
            raise e

    def get_user_by_id(self, user_pk: int) -> User:
        query = f'SELECT {", ".join(self.all_columns)} FROM users WHERE pk=%s'
        try:
            return self._get_user(query, (user_pk,))
        except mysql.connector.Error as e:
            raise e

    def get_user_by_email(self, email: str) -> User:
        query = f'SELECT {", ".join(self.all_columns)} FROM users WHERE email=%s'
        try:
            return self._get_user(query, (email,))
        except mysql.connector.Error as e:
            raise e

    def get_latest_history_id(self, user: User) -> str:
        earlist_unproccessed_history_query = f'SELECT id FROM history WHERE user_pk=%s AND processed_at IS NULL ORDER BY id ASC LIMIT 1;'
        history_variables = (user.pk,)
        try:
            response = self.db.query(earlist_unproccessed_history_query, history_variables)
            history_id = response[0].get('id')
            return history_id
        except mysql.connector.Error as e:
            if e.msg == 'Not found':
                print('No unproccessed history record found')
            else:
                print(f'Failed to retrieve unproccessed history record: {e}')

        history_ids = []

        last_processed_history_query = query = f'SELECT id FROM history WHERE user_pk=%s AND processed_at IS NOT NULL ORDER BY id DESC LIMIT 1;'
        try:
            response = self.db.query(last_processed_history_query, history_variables)
            history_id = response[0].get('id')
            history_ids.append(history_id)
        except mysql.connector.Error as e:
            if e.msg == 'Not found':
                print('No processed history records found')
            else:
                print(f'Failed to retrieve latest processed history record: {e}')

        tables = ['threads', 'messages']
        for table in tables:
            query = f'SELECT history_id FROM {table} WHERE user_pk=%s ORDER BY ABS(history_id) DESC LIMIT 1;'
            variables = (user.pk,)
            response = self.db.query(query, variables)
            history_id = response[0].get('history_id')
            history_ids.append(history_id)

        history_ids.sort(reverse=True)
        return history_ids[0]

    def delete_user(self, user_pk: int):
        query = 'DELETE FROM users WHERE pk=%s'
        response = self.db.query(query, (user_pk,))
        self.db.close()
