import os

my_email = os.getenv('MY_EMAIL')


def check_for_my_email(email: str) -> str:
    if email.find(my_email) >= 0:
        return 'me'
    else:
        return email


def get_my_email() -> str:
    return my_email
