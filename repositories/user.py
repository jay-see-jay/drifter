import os

import mysql.connector
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from flask import Request
from werkzeug.exceptions import HTTPException
from typing import List

from services.database import Database
from utilities.user_utils import get_user_id_from_path
from models.user import User

load_dotenv()


class UserRepo:
    def __init__(self):
        key = bytes(os.getenv('SECRET_KEY'), 'utf-8')
        self.db = Database()
        self.f = Fernet(key)

    def encrypt(self, text: str):
        return self.f.encrypt(bytes(text, 'utf-8'))

    def decrypt(self, text: bytes | None):
        if not text:
            return text

        return self.f.decrypt(text).decode('utf-8')

    def create(self, new_user: User):
        # Ensure date is a datetime object:
        # token_expires_at_date = datetime.strptime(os.getenv('TEMP_TOKEN_EXPIRY'), '%Y-%m-%dT%H:%M:%S.%fZ')
        query = """
            INSERT INTO users (email, access_token, refresh_token, token_expires_at, is_active)
            VALUES (%s, %s, %s, %s, %s)
        """

        encrypted_access_token = self.encrypt(new_user.access_token)
        encrypted_refresh_token = self.encrypt(new_user.refresh_token)
        variables = (
            new_user.email,
            encrypted_access_token,
            encrypted_refresh_token,
            new_user.token_expires_at,
            new_user.is_active
        )

        self.db.query(query, variables)

        self.db.close()

    def get_all(self) -> List[User]:
        columns = [
            'pk',
            'email',
            'is_active',
            'created_at',
            'access_token',
            'refresh_token',
            'token_expires_at',
        ]
        query = f'SELECT {", ".join(columns)} FROM users'
        try:
            response = self.db.query(query, ())
            users: List[User] = []
            for row in response:
                encrypted_access_token = row.get('access_token')
                encrypted_refresh_token = row.get('refresh_token')
                users.append(User(
                    pk=row.get('pk'),
                    email=row.get('email'),
                    is_active=row.get('is_active'),
                    access_token=self.decrypt(encrypted_access_token),
                    refresh_token=self.decrypt(encrypted_refresh_token),
                    token_expires_at=response[0].get('token_expires_at'),
                ))
            return users
        except mysql.connector.Error as e:
            e.msg = 'Failed to get all user emails'
            raise e

    def get(self, query, variables) -> User:
        response: list
        try:
            response = self.db.query(query, variables)
        except mysql.connector.Error as e:
            e.msg = 'User not found'
            raise e

        encrypted_access_token = response[0].get('access_token')
        encrypted_refresh_token = response[0].get('refresh_token')
        return User(
            pk=response[0].get('pk'),
            email=response[0].get('email'),
            is_active=response[0].get('is_active'),
            access_token=self.decrypt(encrypted_access_token),
            refresh_token=self.decrypt(encrypted_refresh_token),
            token_expires_at=response[0].get('token_expires_at'),
        )

    def get_from_request(self, request: Request) -> User:
        user_id = get_user_id_from_path(request)
        if not user_id:
            raise HTTPException('User ID not found in request')

        try:
            return self.get_by_id(user_id)
        except mysql.connector.Error as e:
            raise e

    def get_by_id(self, user_pk: int) -> User:
        columns = [
            'pk',
            'email',
            'is_active',
            'created_at',
            'access_token',
            'refresh_token',
            'token_expires_at',
        ]
        query = f'SELECT {", ".join(columns)} FROM users WHERE pk=%s'
        try:
            return self.get(query, (user_pk,))
        except mysql.connector.Error as e:
            raise e

    def get_by_email(self, email: str) -> User:
        columns = [
            'pk',
            'email',
            'is_active',
            'created_at',
            'access_token',
            'refresh_token',
            'token_expires_at',
        ]
        query = f'SELECT {", ".join(columns)} FROM users WHERE email=%s'
        try:
            return self.get(query, (email,))
        except mysql.connector.Error as e:
            raise e

    def get_latest_history_id(self, user: User) -> str:
        tables = ['threads', 'messages']
        history_ids = []
        for table in tables:
            query = f'SELECT history_id FROM {table} WHERE user_pk=%s ORDER BY history_id DESC LIMIT 1;'
            variables = (user.pk,)
            response = self.db.query(query, variables)
            history_id = response[0].get('history_id')
            history_ids.append(history_id)

        history_ids.sort(reverse=True)
        return history_ids[0]

    def save_credentials(self, user: User, creds: Credentials) -> None:
        encrypted_token = self.encrypt(creds.token)
        encrypted_refresh_token = self.encrypt(creds.refresh_token) if creds.refresh_token else None
        query = """
            UPDATE users
            SET
                access_token = %s,
                refresh_token = %s,
                token_expires_at = %s
            WHERE
                email = %s
        """
        variables = (
            encrypted_token,
            encrypted_refresh_token,
            creds.expiry,
            user.email
        )
        self.db.query(query, variables)
        self.db.close()
        return

    def remove_credentials(self, user: User) -> None:
        query = """
            UPDATE users
            SET
                access_token = NULL,
                refresh_token = NULL,
                token_expires_at = NULL
            WHERE
                email = %s
        """
        variables = (user.email,)
        self.db.query(query, variables)
        self.db.close()

    def delete(self, user_id: int):
        query = """
            DELETE FROM users WHERE pk=%s
        """
        response = self.db.query(query, (user_id,))
        print(response)
        self.db.close()

# To encrypt / decrypt keys
# key = os.getenv('SECRET_KEY')
# 
# cipher_suite = Fernet(key)
# data = b"secret message"  # must be bytes
# 
# cipher_text = cipher_suite.encrypt(data)
# print("Cipher Text:", cipher_text)
# 
# plain_text = cipher_suite.decrypt(cipher_text)
# print("Plain Text:", plain_text)
