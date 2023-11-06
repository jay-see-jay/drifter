import os

from dotenv import load_dotenv
from typing import Optional
from flask import Request

load_dotenv()

my_email = os.getenv('MY_EMAIL')


def check_for_my_email(email: str) -> str:
    if email.find(my_email) >= 0:
        return 'me'
    else:
        return email


def get_my_email() -> str:
    return my_email


def get_user_id_from_path(request: Request) -> Optional[int]:
    path = request.path.strip('/').split('/')
    if path[0] != 'users':
        return None

    user_id = path[1]
    if not user_id.isdigit():
        return None

    return int(user_id)
