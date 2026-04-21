import logging
from openai import AsyncOpenAI

from core.config import settings

logger = logging.getLogger(__name__)


class InvalidImageInputError(ValueError):
    pass


class AIHubService:
    def __init__(self):
        if not settings.app_ai_key:
            raise ValueError("Missing API key")

        self.client = AsyncOpenAI(api_key=settings.app_ai_key)

    async def gentxt(self, request):
        response = await self.client.chat.completions.create(
            model=request.model,
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        return {
            "content": response.choices[0].message.content
        }

    async def gentxt_stream(self, request):
        stream = await self.client.chat.completions.create(
            model=request.model,
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def genimg(self, request):
        return {"images": ["not implemented yet"]}