from langchain_core.runnables import Runnable  

class CallableRunnable(Runnable):
    """
    any_fn: (input: str | dict) -> str | dict
    사용 예: any_fn은 Azure SDK 호출을 래핑한 함수(또는 lambda)여야 합니다.
    """
    def __init__(self, any_fn):
        self.any_fn = any_fn

    def invoke(self, input, **kwargs):
        # LangChain은 invoke에 다양한 입력 형태를 보낼 수 있으므로 필요한 전처리 수행
        # 여기서는 input이 문자열이거나 dict인 경우를 처리
        payload = input if isinstance(input, (str, dict)) else str(input)
        result = self.any_fn(payload, **kwargs)
        return result

    async def ainvoke(self, input, **kwargs):
        # 비동기 SDK를 사용할 경우 대비한 구현 (선택)
        payload = input if isinstance(input, (str, dict)) else str(input)
        coro_or_result = self.any_fn(payload, **kwargs)
        if hasattr(coro_or_result, "__await__"):
            return await coro_or_result
        return coro_or_result