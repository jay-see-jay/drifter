import os
import mysql.connector
from typing import List

from dotenv import load_dotenv

from stubs.internal import Env
from stubs.gmail import GmailLabel

load_dotenv()


class Database:
    def __init__(self,
                 env: Env = 'development'
                 ):
        is_production = env == 'production'

        username = os.getenv('DATABASE_USERNAME_PROD') if is_production else os.getenv('DB_USER_DEV_ADMIN')
        password = os.getenv('DATABASE_PASSWORD_PROD') if is_production else os.getenv('DB_PASS_DEV_ADMIN')
        self.connection = mysql.connector.connect(
            host=os.getenv("DATABASE_HOST"),
            user=username,
            passwd=password,
            db=os.getenv("DATABASE"),
            autocommit=True,
            ssl_verify_identity=True,
            ssl_ca=os.getenv('CERTIFICATE_PATH'),
        )
        self.cursor = self.connection.cursor(dictionary=True)

    def close(self):
        self.cursor.close()
        self.connection.close()

    def ensure_connection(self):
        if not self.connection.is_connected():
            self.cursor.close()
            self.connection.reconnect()
            self.cursor = self.connection.cursor(dictionary=True)

    def query(self, query: str, variables: tuple):
        self.ensure_connection()

        self.cursor.execute(query, variables)
        response = self.cursor.fetchall()
        if len(response) == 0:
            raise mysql.connector.Error('Not found')

        return response

    def insert_one(self, query: str, variables: tuple):
        self.ensure_connection()
        self.cursor.execute(query, variables)

    def insert_many(self, query: str, variables: List[tuple]):
        self.ensure_connection()
        self.cursor.executemany(query, variables)

    @staticmethod
    def create_query(column_names: List[str], table_name: str) -> str:
        columns_str = ', '.join(column_names)
        variables = ['%s'] * len(column_names)
        variables_str = ', '.join(variables)
        return f'INSERT INTO {table_name} ({columns_str}) VALUES ({variables_str})'

    @staticmethod
    def append_string_formatter(string: str) -> str:
        return string + '=%s'

    def create_update_query(
        self,
        column_names: List[str],
        table_name: str,
        filter_columns: List[str],
    ) -> str:

        column_strings = map(self.append_string_formatter, column_names)
        filter_strings = map(self.append_string_formatter, filter_columns)
        return f'UPDATE {table_name} SET {" ".join(column_strings)} WHERE {" AND ".join(filter_strings)}'

    def create_delete_query(self, filter_columns: List[str], table_name: str) -> str:
        filter_strings = map(self.append_string_formatter, filter_columns)
        return f'DELETE FROM {table_name} WHERE {" AND ".join(filter_strings)}'

    @staticmethod
    def filter_changed_columns(existing: dict, updated: dict, columns: List[str]) -> List[str]:
        changed_columns: List[str] = []
        for column in columns:
            if existing.get(column) == updated.get(column):
                continue

            changed_columns.append(column)

        return changed_columns
