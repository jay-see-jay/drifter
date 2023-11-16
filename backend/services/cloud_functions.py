import os
import urllib.request
from typing import Literal, Optional

import google.auth.transport.requests
import google.oauth2.id_token

FunctionName = Literal['sync_gmail']


def select_function_path(function_name) -> Optional[str]:
    function_paths = {
        'sync_gmail': os.getenv('SYNC_GMAIL_FUNCTION'),
    }

    return function_paths.get(function_name, None)


class CloudFunctions:
    def __init__(
        self,
        function_name: Optional[FunctionName] = 'sync_gmail'
    ):
        self.base_path = select_function_path(function_name)

    def sync_gmail(self, user_pk: int):
        endpoint = f'{self.base_path}/users/{user_pk}'
        req = urllib.request.Request(url=endpoint, method='POST')
        auth_req = google.auth.transport.requests.Request()
        id_token = google.oauth2.id_token.fetch_id_token(auth_req, self.base_path)
        req.add_header("Authorization", f"Bearer {id_token}")
        urllib.request.urlopen(req)
