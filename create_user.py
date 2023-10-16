import os
from datetime import datetime

from repositories.user import UserRepo
from stubs.internal import User

from dotenv import load_dotenv

load_dotenv()

user_repo = UserRepo()

user_repo.delete_user(1)

# token_expires_at_date = datetime.strptime(os.getenv('TEMP_TOKEN_EXPIRY'), '%Y-%m-%dT%H:%M:%S.%fZ')
# 
# new_user = User(
#     email=os.getenv('MY_EMAIL'),
#     access_token=os.getenv('TEMP_TOKEN'),
#     refresh_token=os.getenv('TEMP_REFRESH_TOKEN'),
#     token_expires_at=token_expires_at_date
# )
# 
# user_repo.create_user(new_user)
