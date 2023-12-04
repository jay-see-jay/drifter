import os
from typing import Optional
from urllib.error import HTTPError

import mysql.connector
from flask import Request, Response, make_response
from dotenv import load_dotenv
from firebase_functions import identity_fn

from services.cloud_functions import call_cloud_function
from repositories import UserRepo
from models import User

load_dotenv()


def handle_create_user(event: identity_fn.AuthBlockingEvent):
    email = event.data.email
    uid = event.data.uid

    new_user = User(
        email=email,
        clerk_user_id=uid
    )

    user_repo = UserRepo()
    try:
        user_pk = user_repo.create_user(new_user)
        print('New user created.')
        if not user_pk:
            user = user_repo.get_user_by_email(new_user.email)
            user_pk = user.pk
        call_cloud_function('sync_gmail', user_pk)
        print('Triggered Gmail sync')
        call_cloud_function('watch_gmail', user_pk)
        print('Set up watch on Gmail mailbox')
    except mysql.connector.Error as e:
        make_response(f'Failed to store new user {e}', 500)
    except HTTPError as e:
        make_response(f'Could not trigger gmail sync: {e}', 500)

    print('Complete.')
