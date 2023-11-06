import flask
from mysql.connector import Error as MySQLError
from werkzeug.exceptions import HTTPException
from googleapiclient.errors import HttpError

from repositories import UserRepo
from services import Gmail
from models import User


def handle_watch_gmail_mailbox(request: flask.Request) -> flask.Response:
    user_repo = UserRepo()
    user: User
    try:
        user = user_repo.get_from_request(request)
    except MySQLError as e:
        return flask.make_response(e.msg, 404)
    except HTTPException as e:
        return flask.make_response(e.description, 400)

    gmail = Gmail(user)

    try:
        gmail.watch_mailbox()
    except HttpError as e:
        return flask.make_response(f'Failed to watch user\'s mailbox')

    return flask.make_response()
