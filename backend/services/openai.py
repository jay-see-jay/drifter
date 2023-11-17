import os
import openai
from openai import OpenAIError

from dotenv import load_dotenv

from stubs.openai import *
from stubs.internal import *

load_dotenv()


class OpenAI:
    def __init__(self):
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.api = openai

    def chat(self, messages: List[ChatCompletionMessage]) -> Optional[str]:
        try:
            response = self.api.ChatCompletion.create(
                model=Model.GPT3.value,
                messages=messages,
            )  # type: ChatCompletionResponse

            return response['choices'][0]['message']['content']
        except OpenAIError as e:
            print(f'Error getting completion: {e}')
            return None

    def extract_message(self, message: str) -> str:
        prompt = 'Please extract only the new message from the email below, ' \
                 'removing any quotes from earlier messages in the thread.' \
                 'Treat any URLs as plain text, you do not need to access the URL.' \
                 'Do not make any edits to the message, only remove text that is a quote' \
                 'from earlier in the thread. Do not add anything to indicate what you' \
                 'have done, simply present the cleaned message on it\'s own.'
        message: ChatCompletionMessage = {
            'role': 'user',
            'content': f"""
                    {prompt}
                    {message}
                """
        }

        try:
            return self.chat(messages=[message])

        except Exception as e:
            print(f'Issue with extracting the new message from the conversation: {e}')

    def get_draft_reply(self, conversation: List[ParsedMessage]) -> str:
        # TODO: Add first name(s) of recipient to prompt so OpenAI doens't use placeholders
        system_prompt = 'You are managing my email inbox for me and drafting replies to new emails. ' \
                        'Each response should only contain the content of the message to send, and nothing else. ' \
                        'Please don\'t indicate that you are an AI in anyway. Everything you draft will be checked ' \
                        'by me before it is sent.'
        messages: List[ChatCompletionMessage] = [
            {
                'role': 'system',
                'content': system_prompt,
            }
        ]
        for message in conversation:
            role = 'assistant' if message['headers']['email_from'] == 'me' else 'user'
            content = message['body']
            messages.append({
                'role': role,
                'content': content,
            })

        try:
            return self.chat(messages=messages)

        except Exception as e:
            print(f'Issue getting a draft reply to the conversation: {e}')
