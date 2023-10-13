from typing import List, TypedDict


class WatchSubscriptionResponse(TypedDict):
    historyId: str
    expiration: str


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


class GmailMessage:
    def __init__(self,
                 id: str,
                 thread_id: str,
                 label_ids: List[str],
                 snippet: str,
                 history_id: str,
                 internal_date: str,
                 payload: GmailMessagePart,
                 size_estimate: int,
                 raw: str,
                 ) -> None:
        self.id = id
        self.threadId = thread_id
        self.labelIds = label_ids
        self.snippet = snippet
        self.historyId = history_id
        self.internalDate = internal_date
        self.payload = payload
        self.sizeEstimate = size_estimate
        self.raw = raw


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
