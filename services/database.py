import os
import mysql.connector

from dotenv import load_dotenv

from stubs.internal import Env

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
        return self.cursor.fetchall()
