from services.gmail import Gmail

gmail_service = Gmail()

response = gmail_service.get_changed_thread_ids()
print(response)
