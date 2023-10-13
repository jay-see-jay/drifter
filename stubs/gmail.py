from typing import List, TypedDict


class WatchSubscriptionResponse(TypedDict):
    historyId: str
    expiration: str


class MessageData(TypedDict):
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


class GmailMessagePartBody:
    def __init__(self,
                 attachment_id: str,
                 size: int,
                 data: bytes,
                 ) -> None:
        self.attachmentId = attachment_id
        self.size = size
        self.data = data


class GmailHeader:
    def __init__(self,
                 name: str,
                 value: str,
                 ) -> None:
        self.name = name
        self.value = value


class GmailMessagePart:
    def __init__(self,
                 part_id: str,
                 mime_type: str,
                 filename: str,
                 headers: List[GmailHeader],
                 body: GmailMessagePartBody,
                 parts: List['GmailMessagePart'],
                 ) -> None:
        self.partId = part_id
        self.mimeType = mime_type
        self.filename = filename
        self.headers = headers
        self.body = body
        self.parts = parts


class GmailMessageTruncated(TypedDict):
    id: str
    threadId: str


class GmailMessage(GmailMessageTruncated):
    label_ids: List[str]
    snippet: str
    history_id: str
    internal_date: str
    payload: GmailMessagePart
    size_estimate: int
    raw: str


class GmailThread:
    def __init__(self,
                 id: str,
                 snippet: str,
                 history_id: str,
                 messages: List[GmailMessage],
                 ) -> None:
        self.id = id
        self.snippet = snippet
        self.historyId = history_id
        self.messages = messages


class GmailThreadsListResponse:
    def __init__(self,
                 threads: List['GmailThread'],
                 next_page_token: str,
                 result_estimate_size: int,
                 ) -> None:
        self.threads = threads
        self.nextPageToken = next_page_token
        self.resultEstimateSize = result_estimate_size
