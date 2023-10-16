import os
import mysql.connector

from dotenv import load_dotenv

load_dotenv()


class Database:
    def __init__(self):
        self.connection = mysql.connector.connect(
            host=os.getenv("DATABASE_HOST"),
            user=os.getenv("DATABASE_USERNAME"),
            passwd=os.getenv("DATABASE_PASSWORD"),
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
        self.cursor.execute(query, variables)
        return self.cursor.fetchall()
