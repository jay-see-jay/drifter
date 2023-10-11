from typing import Literal, List

FinishReason = Literal['stop', 'length', 'content_filter', 'function_call']


class OpenAIUsage:
    def __init__(self,
                 completion_tokens: int,
                 prompt_tokens: int,
                 total_tokens: int,
                 ):
        self.completion_tokens = completion_tokens
        self.prompt_tokens = prompt_tokens
        self.total_tokens = total_tokens


class ChatCompletionMessage:
    def __init__(self,
                 role: str,
                 content: str,
                 ):
        self.role = role
        self.content = content


class ChatCompletionChoices:
    def __init__(self,
                 index: int,
                 message: ChatCompletionMessage,
                 finish_reason: FinishReason,
                 ):
        self.index = index
        self.message = message
        self.finish_reason = finish_reason


class ChatCompletion:
    def __init__(self,
                 id: str,
                 object: str,
                 created: int,
                 model: str,
                 choices: List['ChatCompletionChoices'],
                 usage: OpenAIUsage,
                 ):
        self.id = id
        self.object = object
        self.created = created
        self.model = model
        self.choices = choices
        self.usage = usage
