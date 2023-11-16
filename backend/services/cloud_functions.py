import os
import urllib.request
from typing import Literal, Optional

import google.auth.transport.requests
import google.oauth2.id_token

FunctionName = Literal['sync_gmail', 'watch_gmail']


def select_function_path(function_name) -> Optional[str]:
    function_paths = {
        'sync_gmail': os.getenv('SYNC_GMAIL_FUNCTION'),
        'watch_gmail': os.getenv('WATCH_GMAIL_FUNCTION')
    }

    return function_paths.get(function_name, None)


def call_cloud_function(function_name: FunctionName, user_pk: int):
    base_path = select_function_path(function_name)
    endpoint = f'{base_path}/users/{user_pk}'
    req = urllib.request.Request(url=endpoint, method='POST')
    auth_req = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, base_path)
    req.add_header("Authorization", f"Bearer {id_token}")
    urllib.request.urlopen(req)
