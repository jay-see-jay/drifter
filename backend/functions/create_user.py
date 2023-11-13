import os
from flask import Request, Response, make_response
from svix.webhooks import Webhook, WebhookVerificationError
from dotenv import load_dotenv

from stubs.clerk import *

load_dotenv()


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

    print('msg', msg)

    return make_response()
