from datetime import datetime
from typing import Optional, List, Union, Tuple
from stubs import GmailMessagePartResponse
from models import MessagePart


def flatten_parts(
    part: GmailMessagePartResponse,
    parts: List[GmailMessagePartResponse]
):
    new_part: GmailMessagePartResponse = {
        'partId': part.get('partId'),
        'mimeType': part.get('mimeType'),
        'filename': part.get('filename'),
        'headers': part.get('headers'),
        'body': part.get('body'),
        'parts': None,
    }
    parts.append(new_part)
    child_parts = part.get('parts')
    if child_parts:
        for child_part in child_parts:
            flatten_parts(child_part, parts)


class Message:
    def __init__(
        self,
        message_id: str,
        history_id: str,
        payload: Optional[GmailMessagePartResponse] = None,
        label_ids: Optional[List[str]] = None,
        snippet: Optional[str] = None,
        internal_date: Optional[Union[datetime, str]] = None,
        size_estimate: Optional[int] = None,
        added_history_id: Optional[str] = None,
        deleted_history_id: Optional[str] = None,
    ):
        self.message_id = message_id
        self.history_id = history_id
        self.label_ids = label_ids
        self.snippet = snippet
        if isinstance(internal_date, datetime):
            self.internal_date = internal_date
        else:
            self.internal_date = datetime.fromtimestamp(float(internal_date) / 1000)
        self.size_estimate = size_estimate
        self.added_history_id = added_history_id
        self.deleted_history_id = deleted_history_id
        flattened_parts: List[GmailMessagePartResponse] = []
        flatten_parts(payload, flattened_parts)
        self.parts = [
            MessagePart(
                part_id=part.get('partId'),
                mime_type=part.get('mimeType'),
                filename=part.get('filename'),
                headers=part.get('headers'),
                body=part.get('body'),
            )
            for part in flattened_parts
        ]
        self.create_columns = [
            'id',
            'snippet',
            'user_pk',
            'thread_id',
            'history_id',
            'internal_date',
            'added_history_id',
            'size_estimate',
        ]


MessageCreateVariablesType = Tuple[str, str, int, str, str, datetime, str, int]
