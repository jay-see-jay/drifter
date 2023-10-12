from services.gmail import Gmail

gmail_service = Gmail()

response = gmail_service.get_history()
print(response)
