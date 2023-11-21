from googleapiclient.errors import HttpError
from repositories import UserRepo, HistoryRepo
from services import Gmail, Clerk


def handle_refresh_mailbox_sub() -> None:
    user_repo = UserRepo()
    users = user_repo.get_all_users()
    clerk_service = Clerk()
    for user in users:
        oauth = clerk_service.get_oauth_token(user.clerk_user_id)
        gmail = Gmail(user, oauth)
        history_repo = HistoryRepo(user)

        try:
            response = gmail.watch_mailbox()
            history_repo.create_watch(response)
        except HttpError:
            print(f'Failed to refresh watch for user: {user.pk}')
