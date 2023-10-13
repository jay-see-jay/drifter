from cloudevents.http import CloudEvent

from services.gmail import Gmail


def handle_watch_gmail_messages(cloud_event: CloudEvent) -> None:
    cloud_event_data = Gmail.decode_cloud_event(cloud_event)

    gmail_service = Gmail()
    changed_thread_ids = gmail_service.get_changed_thread_ids(cloud_event_data["historyId"])
    # TODO: changed_thread_ids now contains a set of thread_ids to sync with the database,
    #       determine the ones to reply to and create the replies.


if __name__ == "__main__":
    test_attributes = {
        'specversion': '1.0',
        'id': '8872658318367077',
        'source': '//pubsub.googleapis.com/projects/jayseejay-1/topics/gmail-change',
        'type': 'google.cloud.pubsub.topic.v1.messagePublished',
        'datacontenttype': 'application/json',
        'time': '2023-10-13T12:00:14.631Z'
    }
    test_data = {
        'message': {
            'data': 'eyJlbWFpbEFkZHJlc3MiOiIxMDNqY2pAZ21haWwuY29tIiwiaGlzdG9yeUlkIjoxMjU3NzZ9',
            'messageId': '8872658318367077',
            'message_id': '8872658318367077',
            'publishTime': '2023-10-13T12:00:14.631Z',
            'publish_time': '2023-10-13T12:00:14.631Z'
        },
        'subscription': 'projects/jayseejay-1/subscriptions/eventarc-europe-west2-watch-gmail-messages-176919-sub-793'
    }

    test_cloud_event = CloudEvent.create(test_attributes, test_data)
    handle_watch_gmail_messages(test_cloud_event)
