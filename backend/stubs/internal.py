from typing import TypedDict, Literal, Optional
from datetime import datetime

Env = Literal['production', 'development']


class ParsedMessageHeaders(TypedDict):
    email_from: str
    email_to: str
    subject: str


class ParsedMessage(TypedDict):
    index: int
    headers: ParsedMessageHeaders
    body: str


class Migration:
    def __init__(self,
                 name: str,
                 date: datetime,
                 completed_at: Optional[datetime],
                 ):
        self.name = name
        self.date = date
        self.date_name = f'{date.strftime("%Y-%m-%d")}_{name}'
        self.completed_at = completed_at
