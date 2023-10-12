import os

from services.gmail import Gmail

from googleapiclient.errors import HttpError

gmail_service = Gmail().api

try:
    cloud_project = os.getenv('GOOGLE_PROJECT_ID')
    pubsub_topic = os.getenv('GOOGLE_PUBSUB_TOPIC')

    request = {
        'labelIds': ['INBOX'],
        'topicName': f'projects/{cloud_project}/topics/{pubsub_topic}',
        'labelFilterBehavior': 'INCLUDE'
    }
    print('Creating subscription...')
    response = gmail_service.users().watch(userId='me', body=request).execute()
    # response = gmail_service.users().stop(userId='me').execute()
    print(response)
except HttpError as e:
    print(f'Failed to create subscription to users mailbox: {e}')
