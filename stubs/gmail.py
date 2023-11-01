from typing import List, TypedDict, Literal, Optional
from datetime import datetime


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
    partId: Optional[str]
    mimeType: str
    filename: str
    headers: List[GmailHeader]
    body: GmailMessagePartBody
    parts: List['GmailMessagePart']


class GmailMessage:
    def __init__(self,
                 message_id: str,
                 thread_id: str,
                 label_ids: List[str],
                 snippet: str,
                 history_id: str,
                 internal_date: str,
                 payload: GmailMessagePart,
                 size_estimate: int,
                 ):
        self.message_id = message_id
        self.thread_id = thread_id
        self.label_ids = label_ids
        self.snippet = snippet
        self.history_id = history_id
        self.internal_date = datetime.fromtimestamp(float(internal_date) / 1000)
        self.payload = payload
        self.size_estimate = size_estimate


class GmailThread:
    def __init__(self,
                 thread_id: str,
                 history_id: str,
                 messages: List[dict],
                 snippet: Optional[str] = None,
                 ):
        self.thread_id = thread_id
        self.snippet = snippet
        self.history_id = history_id
        self.messages = [
            GmailMessage(
                message_id=message.get('id'),
                thread_id=message.get('threadId'),
                label_ids=message.get('labelIds'),
                snippet=message.get('snippet'),
                history_id=message.get('historyId'),
                internal_date=message.get('internalDate'),
                payload=message.get('payload'),
                size_estimate=message.get('sizeEstimate'),
            )
            for message in messages
        ]


class GmailThreadsListResponse(TypedDict):
    thread_ids: List[str]
    next_page_token: str


MessageListVisibility = Literal['show', 'hide']
LabelListVisibility = Literal['labelShow', 'labelShowIfUnread', 'labelHide']
GmailLabelType = Literal['system', 'user']


class GmailLabelColor:
    def __init__(self,
                 text_color: str = None,
                 background_color: str = None,
                 ):
        self.text_color = text_color
        self.background_color = background_color


class GmailLabel:
    def __init__(self,
                 label_id: str,
                 name: str,
                 label_type: GmailLabelType,
                 messages_total: int,
                 messages_unread: int,
                 threads_total: int,
                 threads_unread: int,
                 message_list_visibility: Optional[MessageListVisibility] = None,
                 label_list_visibility: Optional[LabelListVisibility] = None,
                 color: Optional[dict] = None,
                 ):
        self.label_id = label_id
        self.name = name
        self.message_list_visibility = message_list_visibility
        self.label_list_visibility = label_list_visibility
        self.label_type = label_type
        self.messages_total = messages_total
        self.messages_unread = messages_unread
        self.threads_total = threads_total
        self.threads_unread = threads_unread
        if not color:
            self.color = GmailLabelColor()
        else:
            self.color = GmailLabelColor(color.get('textColor'), color.get('backgroundColor'))
