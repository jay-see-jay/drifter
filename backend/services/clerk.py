import os
import requests
from typing import List

from dotenv import load_dotenv

from stubs.clerk import OAuthAccessToken, ClerkError

load_dotenv()


class Clerk:
    def __init__(self):
        token = os.getenv('CLERK_SECRET_KEY')
        self.headers = {
            'Authorization': f'Bearer {token}'
        }
        self.url = 'https://api.clerk.com/v1'

    def get_oauth_token(self, user_id: str, provider: str = 'oauth_google'):
        url = f'{self.url}/users/{user_id}/oauth_access_tokens/{provider}'
        response = requests.get(url, headers=self.headers).json()

        if isinstance(response, dict) and 'errors' in response:
            errors = response['errors']
            if errors:
                first_error = errors[0]
                raise ClerkError(first_error.get('message'))

        if not isinstance(response, list) or len(response) == 0:
            raise ClerkError('Could not retrieve user\'s access token from Clerk')

        first_row = response[0]
        return OAuthAccessToken(
            object=first_row.get('object'),
            token=first_row.get('token'),
            provider=first_row.get('provider'),
            public_metadata=first_row.get('public_metadata'),
            scopes=first_row.get('scopes'),
            label=first_row.get('label'),
            token_secret=first_row.get('token_secret'),
        )
