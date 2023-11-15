import os
import requests
from typing import List

from dotenv import load_dotenv

from stubs.clerk import OAuthAccessToken

load_dotenv()


class Clerk:
    def __init__(self):
        token = os.getenv('CLERK_SECRET_KEY')
        self.headers = {
            'Authorization': f'Bearer {token}'
        }
        self.url = 'https://api.clerk.com/v1'

    def get_oauth_token(self, user_id: str, provider: str = 'oauth_google') -> str:
        url = f'{self.url}/users/{user_id}/oauth_access_tokens/{provider}'
        response = requests.post(url, headers=self.headers).json()  # type: List[OAuthAccessToken]
        return response[0]['token']
