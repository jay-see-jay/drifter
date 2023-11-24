from models import Draft
from stubs import GmailDraftResponse
from services import Database


def create_draft(draft_dict: GmailDraftResponse) -> Draft:
    draft_message = draft_dict.get('message')
    return Draft(
        database=Database(),
        draft_id=draft_dict.get('id'),
        message_id=draft_message.get('id'),
        thread_id=draft_message.get('threadId'),
        label_ids=draft_message.get('labelIds'),
    )
