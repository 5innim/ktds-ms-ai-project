import os
from openai import AzureOpenAI
from langchain_core.runnables import Runnable
from langchain_core.prompt_values import ChatPromptValue
from langchain_core.messages import BaseMessage


def _message_to_dict(message: BaseMessage) -> dict:
    """Converts a LangChain message to a dictionary for the OpenAI API."""
    if message.type == "human":
        role = "user"
    elif message.type == "ai":
        role = "assistant"
    elif message.type == "system":
        role = "system"
    else:
        role = message.type
    return {"role": role, "content": message.content}


def azure_call(payload, **kwargs):
    azure_openai_key = os.environ.get("AZURE_OPENAI_KEY")
    azure_openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "https://5innim-openai-1030.openai.azure.com/")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "5innim-gpt-4.1")

    if not deployment:
        raise ValueError("AZURE_OPENAI_DEPLOYMENT environment variable is not set.")

    client = AzureOpenAI(
        api_version=api_version,
        azure_endpoint=azure_openai_endpoint,
        api_key=azure_openai_key,
    )

    if isinstance(payload, ChatPromptValue):
        messages = [_message_to_dict(msg) for msg in payload.to_messages()]
    elif isinstance(payload, list) and all(isinstance(m, BaseMessage) for m in payload):
        messages = [_message_to_dict(m) for m in payload]
    elif isinstance(payload, str):
        messages = [{"role": "user", "content": payload}]
    else:
        raise TypeError(f"Unsupported payload type: {type(payload)}")

    result = client.chat.completions.create(model=deployment, messages=messages, **kwargs)
    
    return result.choices[0].message.content


class CallableRunnable(Runnable):
    """
    any_fn: (input: any) -> any
    사용 예: any_fn은 Azure SDK 호출을 래핑한 함수(또는 lambda)여야 합니다.
    """
    def __init__(self, any_fn):
        self.any_fn = any_fn

    def invoke(self, input, **kwargs):
        # LangChain은 invoke에 다양한 입력 형태를 보낼 수 있으므로,
        # 래핑된 함수(any_fn)가 이를 적절히 처리해야 합니다.
        result = self.any_fn(input, **kwargs)
        return result

    async def ainvoke(self, input, **kwargs):
        # 비동기 SDK를 사용할 경우 대비한 구현 (선택)
        coro_or_result = self.any_fn(input, **kwargs)
        if hasattr(coro_or_result, "__await__"):
            return await coro_or_result
        return coro_or_result