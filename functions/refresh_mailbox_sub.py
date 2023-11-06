from googleapiclient.errors import HttpError
from repositories import UserRepo
from services import Gmail


def handle_refresh_mailbox_sub() -> None:
    user_repo = UserRepo()
    users = user_repo.get_all()
    for user in users:
        gmail = Gmail(user)
        try:
            gmail.watch_mailbox()
        except HttpError:
            print(f'Failed to refresh watch for user: {user.pk}')
