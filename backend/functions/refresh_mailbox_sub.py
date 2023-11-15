from googleapiclient.errors import HttpError
from repositories import UserRepo
from services import Gmail, Clerk


def handle_refresh_mailbox_sub() -> None:
    user_repo = UserRepo()
    users = user_repo.get_all_users()
    clerk_service = Clerk()
    for user in users:
        oauth = clerk_service.get_oauth_token(user.clerk_user_id)
        gmail = Gmail(user, oauth)
        try:
            gmail.watch_mailbox()
        except HttpError:
            print(f'Failed to refresh watch for user: {user.pk}')
