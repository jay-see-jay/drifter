from typing import List


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


# Can a class reference itself? https://developers.google.com/gmail/api/reference/rest/v1/users.messages#Message.MessagePart
class GmailMessagePart:
    def __init__(self,
                 part_id: str,
                 mime_type: str,
                 filename: str,
                 headers: List[GmailHeader],
                 body: List[GmailMessagePartBody],
                 ) -> None:
        self.partId = part_id
        self.mimeType = mime_type
        self.filename = filename
        self.headers = headers
        self.body = body


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
