from datetime import datetime
from typing import List

from repositories import *
from models import User


class MessageRepos:
    def __init__(
        self,
        thread_repo: ThreadRepo,
        message_repo: MessageRepo,
        message_part_repo: MessagePartRepo,
        header_repo: HeaderRepo,
        label_repo: LabelRepo,
    ):
        self.thread = thread_repo
        self.message = message_repo
        self.part = message_part_repo
        self.header = header_repo
        self.label = label_repo


# TODO : MessagePart class
# TODO : Header class

class Message:
    def __init__(
        self,
        repos: MessageRepos,
        message_id: str,
        thread_id: str,
        label_ids: List[str],
        snippet: str,
        history_id: str,
        internal_date: datetime,
        size_estimate: int,
        payload: dict = None,
        added_history_id: str = None,
        deleted_history_id: str = None,
    ):
        self.repos = repos
        self.thread_id = thread_id
        self.message_id = message_id
        self.label_ids = label_ids
        self.snippet = snippet
        self.history_id = history_id
        self.internal_date = internal_date
        self.size_estimate = size_estimate
        self.payload = payload
        self.added_history_id = added_history_id
        self.deleted_history_id = deleted_history_id


def create_message(user: User) -> Message:
    thread_repo = ThreadRepo(user)
    message_repo = MessageRepo(user)
    message_part_repo = MessagePartRepo()
    header_repo = HeaderRepo()
    label_repo = LabelRepo(user)
    repos = MessageRepos(
        thread_repo,
        message_repo,
        message_part_repo,
        header_repo,
        label_repo,
    )
    return Message(repos)
