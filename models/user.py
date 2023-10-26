from datetime import datetime


class User:
    def __init__(self,
                 email: str,
                 access_token: str,
                 refresh_token: str,
                 token_expires_at: datetime,
                 is_active: bool = False,
                 ):
        self.email = email
        self.is_active = is_active
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expires_at = token_expires_at
