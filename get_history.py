from services.gmail import get_gmail_service

from googleapiclient.errors import HttpError

gmail_service = get_gmail_service()

try:
    response = gmail_service.users().history().list(userId='me', startHistoryId='125125').execute()
    print(response)
except HttpError as e:
    print(f'Failed to get a list of changes to mailbox: {e}')
