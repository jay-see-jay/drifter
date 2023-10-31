from typing import List, TypedDict


class WatchSubscriptionResponse(TypedDict):
    historyId: str
    expiration: str


class SubscriptionMessageData(TypedDict):
    emailAddress: str
    historyId: str


class DictWithId(TypedDict):
    id: str


class History(DictWithId, total=False):
    messages: dict
    messagesAdded: dict
    messagesDeleted: dict
    labelsAdded: dict
    labelsRemoved: dict


class HistoryResponse(TypedDict):
    history: List[History]
    nextPageToken: str
    historyId: str


class GmailMessagePartBody(TypedDict):
    attachmentId: str
    size: int
    data: bytes


class GmailHeader(TypedDict):
    name: str
    value: str


class GmailMessagePart(TypedDict):
    partId: str | None
    mimeType: str
    filename: str
    headers: List[GmailHeader]
    body: GmailMessagePartBody
    parts: List['GmailMessagePart']


class GmailMessageTruncated(TypedDict):
    id: str
    threadId: str


class GmailMessage(GmailMessageTruncated):
    labelIds: List[str]
    snippet: str
    historyId: str
    internalDate: str
    payload: GmailMessagePart
    sizeEstimate: int
    raw: str | None


class GmailThread(TypedDict):
    id: str
    snippet: str | None
    historyId: str
    messages: List[GmailMessage]


class GmailThreadsListResponse(TypedDict):
    threads: List[GmailThread]
    nextPageToken: str
    resultSizeEstimate: int
