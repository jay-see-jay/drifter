from typing import Literal, List, TypedDict
from enum import Enum

FinishReason = Literal['stop', 'length', 'content_filter', 'function_call']

Role = Literal['system', 'user', 'assistant']


class Model(Enum):
    GPT3 = 'gpt-3.5-turbo'


class OpenAIUsage:
    def __init__(self,
                 completion_tokens: int,
                 prompt_tokens: int,
                 total_tokens: int,
                 ):
        self.completion_tokens = completion_tokens
        self.prompt_tokens = prompt_tokens
        self.total_tokens = total_tokens


class ChatCompletionMessage(TypedDict):
    role: Role
    content: str


class ChatCompletionChoices(TypedDict):
    index: int
    message: ChatCompletionMessage
    finish_reason: FinishReason


class ChatCompletionResponse(TypedDict):
    id: str
    object: str
    created: int
    model: str
    choices: List[ChatCompletionChoices]
    usage: OpenAIUsage
