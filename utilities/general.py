import json
from typing import List, Dict, Set
from stubs import GmailMessage, GmailMessagePart, GmailHeader


def get_value_or_fail(data: dict, key: str) -> str:
    value = data.get(key)
    if not value:
        raise Exception(f'Could not extract {key}')
    else:
        return value


def print_object(obj: object) -> None:
    print(json.dumps(vars(obj), default=lambda x: x.__dict__))


def create_label_messages_dict(messages: List[GmailMessage]) -> Dict[str, Set[str]]:
    label_messages: Dict[str, Set[str]] = dict()
    for msg in messages:
        for label_id in msg.label_ids:  # type: str
            if label_id not in label_messages:
                label_messages[label_id] = set()

                label_messages[label_id].add(msg.message_id)

        return label_messages


def process_message_part(part: GmailMessagePart) -> tuple[List[GmailHeader], List[GmailMessagePart]]:
    headers: List[GmailHeader] = []
    parts: List[GmailMessagePart] = []
    headers.extend(part.headers)
    parts.append(part)
    child_parts = part.parts
    if child_parts:
        for child_part in child_parts:
            child_part_headers, child_part_parts = process_message_part(child_part)
            headers.extend(child_part_headers)
            parts.extend(child_part_parts)

    return headers, parts


def process_message_parts(messages: List[GmailMessage]) -> tuple[List[GmailHeader], List[GmailMessagePart]]:
    headers: List[GmailHeader] = []
    parts: List[GmailMessagePart] = []
    for message in messages:  # type: GmailMessage
        part_headers, part_child_parts = process_message_part(message.payload)
        headers.extend(part_headers)
        parts.extend(part_child_parts)

    return headers, parts
