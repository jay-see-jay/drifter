from typing import Optional


class User:
    def __init__(self,
                 email: str,
                 clerk_user_id: str,
                 pk: Optional[int] = None,
                 is_active: bool = False,
                 ):
        self.pk = pk
        self.email = email
        self.is_active = is_active
        self.clerk_user_id = clerk_user_id
