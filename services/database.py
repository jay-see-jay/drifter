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

    def query(self, query: str, variables: tuple):
        try:
            self.cursor.execute(query, variables)
            return self.cursor.fetchall()
        except Exception as e:
            print(f'Failed to execute query: {e}')
