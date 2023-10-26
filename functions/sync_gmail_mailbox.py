import os

from dotenv import load_dotenv

from services.gmail import Gmail
from models.user import User
from repositories.user import UserRepo

load_dotenv()


def handle_sync_gmail_mailbox(request):
    user_repo = UserRepo()
    # TODO: Extract user id or email from request
    user = user_repo.get(os.getenv('MY_EMAIL'))
    user = User(
        email=user.email,
        access_token=user.access_token,
        refresh_token=user.refresh_token,
        token_expires_at=user.token_expires_at
    )
    gmail = Gmail(user)
    threads = gmail.get_threads()
    # print(threads)


if __name__ == "__main__":
    handle_sync_gmail_mailbox({})
