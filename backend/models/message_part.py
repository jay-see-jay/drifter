from typing import Optional, List


class MessageHeader:
    def __init__(
        self,
        name: str,
        value: str,
    ):
        self.name = name
        self.value = value


class MessagePartBody:
    def __init__(
        self,
        size: int,
        data: bytes,
        attachment_id: Optional[str] = None,
    ):
        self.attachment_id = attachment_id
        self.size = size
        self.data = data


class MessagePart:
    def __init__(
        self,
        part_id: Optional[str],
        mime_type: str,
        filename: str,
        headers: List[dict],
        body: dict,
    ):
        self.part_id = part_id
        self.mime_type = mime_type
        self.filename = filename
        self.headers = [
            MessageHeader(
                name=header.get('name'),
                value=header.get('value'),
            )
            for header in headers
        ]
        self.body = MessagePartBody(
            size=body.get('size'),
            data=body.get('data'),
            attachment_id=body.get('attachmentId'),
        )
