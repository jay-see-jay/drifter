import flask
from mysql.connector import Error as MySQLError
from werkzeug.exceptions import HTTPException
from googleapiclient.errors import HttpError

from repositories import UserRepo, HistoryRepo
from services import Gmail, Clerk


def handle_watch_gmail(request: flask.Request) -> flask.Response:
    user_repo = UserRepo()
    try:
        user = user_repo.get_user_from_request(request)
        oauth = Clerk().get_oauth_token(user.clerk_user_id)
    except MySQLError as e:
        return flask.make_response(e.msg, 404)
    except HTTPException as e:
        return flask.make_response(e.description, 400)

    gmail = Gmail(user, oauth)
    history_repo = HistoryRepo(user)

    try:
        response = gmail.watch_mailbox()
        history_repo.create_watch(response)
    except HttpError as e:
        return flask.make_response(f'Failed to watch user\'s mailbox')

    return flask.make_response()
