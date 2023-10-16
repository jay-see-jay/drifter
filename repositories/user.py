# from cryptography.fernet import Fernet

from services.database import Database
from stubs.internal import User


class UserRepo:
    def __init__(self):
        self.db = Database()

    def create_user(self, new_user: User):
        # guest_name = "Brittany"
        # email = "brittany@yahoo.com"
        query = """
            INSERT INTO users (email, access_token, refresh_token, token_expires_at, is_active)
            VALUES (%s, %s, %s, %s, %s)
        """
        variables = (
            new_user.email,
            new_user.access_token,
            new_user.refresh_token,
            new_user.token_expires_at,
            new_user.is_active
        )

        response = self.db.query(query, variables)

        print(response)

        self.db.close()

    def delete_user(self, user_id: int):
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
