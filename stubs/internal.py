from typing import TypedDict


class ParsedMessageHeaders(TypedDict):
    email_from: str
    email_to: str
    subject: str


class ParsedMessage(TypedDict):
    index: int
    headers: ParsedMessageHeaders
    body: str
