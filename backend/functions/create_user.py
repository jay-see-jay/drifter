import os
from typing import Optional

import mysql.connector
from flask import Request, Response, make_response
from svix.webhooks import Webhook, WebhookVerificationError
from dotenv import load_dotenv

from repositories import UserRepo
from models import User
from stubs.clerk import *

load_dotenv()


def extract_primary_email_address(event_data: UserCreatedEventData) -> str:
    primary_email_address_id = event_data.get('primary_email_address_id')
    email_addresses = event_data.get('email_addresses', [])
    primary_email_address: Optional[str] = None

    for email_address in email_addresses:
        email_address_id = email_address.get('id')
        if not email_address_id:
            continue

        if email_address_id == primary_email_address_id:
            primary_email_address = email_address['email_address']
            break

    if not primary_email_address:
        raise Exception('Failed to identify email address')

    return primary_email_address


def handle_create_user(request: Request) -> Response:
    path = request.path
    if path != '/users':
        return make_response('Incorrect path', 404)

    headers = request.headers
    payload = request.get_data()

    try:
        wh = Webhook(os.getenv('CLERK_WEBHOOK_SECRET'))
        msg = wh.verify(payload, headers)  # type: UserCreatedEvent
    except WebhookVerificationError as e:
        return make_response(f'Webhook verfication failed: {e}', 400)

    msg_data = msg.get('data')
    if not msg_data:
        return make_response('User created event does not contain any data', 400)

    try:
        primary_email_address = extract_primary_email_address(msg_data)
        clerk_user_id = msg_data['id']
    except Exception as e:
        return make_response(e, 400)

    new_user = User(
        email=primary_email_address,
        clerk_user_id=clerk_user_id
    )

    user_repo = UserRepo()
    try:
        user_repo.create_user(new_user)
    except mysql.connector.Error as e:
        make_response('Failed to store new user', 400)

    return make_response()
