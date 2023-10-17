import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv

from services.database import Database
from stubs.internal import User

load_dotenv()


class UserRepo:
    def __init__(self):
        key = bytes(os.getenv('SECRET_KEY'), 'utf-8')
        self.db = Database()
        self.f = Fernet(key)

    def encrypt(self, text: str):
        return self.f.encrypt(bytes(text, 'utf-8'))

    def decrypt(self, text: bytes):
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

        response = self.db.query(query, variables)

        print(response)

        self.db.close()

    def get(self, email: str):
        query = """
            SELECT email, is_active, created_at, access_token, refresh_token, token_expires_at
            FROM users
            WHERE email=%s
        """
        response = self.db.query(query, (email,))
        encrypted_access_token = response[0].get('access_token')
        encrypted_refresh_token = response[0].get('refresh_token')
        user = User(
            email=response[0].get('email'),
            is_active=response[0].get('is_active'),
            access_token=self.decrypt(encrypted_access_token),
            refresh_token=self.decrypt(encrypted_refresh_token),
            token_expires_at=response[0].get('token_expires_at'),
        )
        self.db.close()
        return user

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
