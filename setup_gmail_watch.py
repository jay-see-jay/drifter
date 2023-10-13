from services.gmail import Gmail

from googleapiclient.errors import HttpError

gmail_service = Gmail()

try:
    response = gmail_service.watch_mailbox()
    # response = gmail_service.unwatch_mailbox()
    print(response)
except HttpError as e:
    print(f'Failed to create subscription to users mailbox: {e}')
