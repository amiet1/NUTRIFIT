"""
AI Hub service layer implementation.
Provides Generate Text (gentxt) and Generate Image (genimg) capabilities using the OpenAI SDK.
"""

import base64
import io
import logging
from typing import AsyncGenerator

from core.config import settings
from openai import AsyncOpenAI
from schemas.aihub import GenImgRequest, GenImgResponse, GenTxtRequest, GenTxtResponse

logger = logging.getLogger(__name__)


class InvalidImageInputError(ValueError):
    """Raised when the provided image input cannot be parsed."""


class AIHubService:
    """AI Hub service class that wraps LLM calls based on the OpenAI SDK."""

    def __init__(self):
        # FIX: Point to the correct key name from your .env / settings
        self.api_key = getattr(settings, "app_ai_key", None)
        
        if not self.api_key:
            raise ValueError("AI service not configured. Set APP_AI_KEY in your .env file.")

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=getattr(settings, "app_ai_base_url", "https://api.openai.com/v1").rstrip("/"),
        )

    async def gentxt(self, request: GenTxtRequest) -> GenTxtResponse:
        """Generate Text API (non-streaming)."""
        try:
            # THE BRAIN: Inject the Nutritionist Personality here
            system_message = {
                "role": "system",
                "content": (
                    "You are the NutriFit AI Assistant, an expert nutritionist and fitness coach. "
                    "Provide specific, data-backed advice on macros, calories, and meal plans. "
                    "If a user provides height/weight, calculate their BMR and TDEE automatically."
                )
            }
            
            # Combine the system personality with the user's messages
            messages = [system_message] + [self._convert_message(msg) for msg in request.messages]

            response = await self.client.chat.completions.create(
                model=request.model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=False,
            )
        
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"gentxt_stream error: {e}")
            raise

    @staticmethod
    def _extract_image_ref(item: object) -> str:
        """Extract an image reference from response."""
        if isinstance(item, dict):
            url = item.get("url")
            if url: return url
            b64_json = item.get("b64_json")
            if b64_json: return f"data:image/png;base64,{b64_json}"
        else:
            url = getattr(item, "url", None)
            if url: return url
            b64_json = getattr(item, "b64_json", None)
            if b64_json: return f"data:image/png;base64,{b64_json}"
        raise RuntimeError("Neither url nor b64_json found in response")

    @staticmethod
    def _parse_data_uri(data_uri: str) -> tuple[bytes, str]:
        """Parse a base64 data URI."""
        if "," not in data_uri:
            raise InvalidImageInputError("Invalid data URI: missing ',' separator.")
        header, b64_data = data_uri.split(",", 1)
        content_type = "image/png"
        if header.startswith("data:"):
            meta = header[5:]
            if ";" in meta:
                maybe_type = meta.split(";", 1)[0].strip()
                if maybe_type: content_type = maybe_type
        try:
            return base64.b64decode(b64_data), content_type
        except Exception as e:
            raise InvalidImageInputError("Invalid base64 data.") from e

    @staticmethod
    def _filename_from_content_type(content_type: str, name_prefix: str = "image") -> str:
        ct = (content_type or "").lower()
        ext = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}.get(ct, "png")
        return f"{name_prefix}.{ext}"

    async def _image_str_to_upload_file(self, image: str, name_prefix: str = "image") -> io.BytesIO:
        image = (image or "").strip()
        if not image.startswith("data:"):
            raise InvalidImageInputError("Only base64 data URI is supported.")
        image_bytes, content_type = self._parse_data_uri(image)
        upload = io.BytesIO(image_bytes)
        upload.name = self._filename_from_content_type(content_type, name_prefix=name_prefix)
        return upload

    async def _image_input_to_upload_files(self, image_input: str | list[str]) -> list[io.BytesIO]:
        images = [image_input] if isinstance(image_input, str) else image_input
        upload_files = []
        for idx, img in enumerate(images):
            upload_files.append(await self._image_str_to_upload_file(img, name_prefix=f"image_{idx + 1}"))
        return upload_files

    async def genimg(self, request: GenImgRequest) -> GenImgResponse:
        """Generate or Edit Image API."""
        try:
            if request.image:
                image_files = await self._image_input_to_upload_files(request.image)
                image_param = image_files[0] if len(image_files) == 1 else image_files
                response = await self.client.images.edit(
                    model=request.model,
                    image=image_param,
                    prompt=request.prompt,
                    size=request.size,
                    n=request.n,
                )
            else:
                response = await self.client.images.generate(
                    model=request.model,
                    prompt=request.prompt,
                    size=request.size,
                    quality=request.quality,
                    n=request.n,
                )

            revised_prompt = response.data[0].revised_prompt if response.data else None
            images = [self._extract_image_ref(item) for item in response.data]

            return GenImgResponse(
                images=images,
                model=request.model,
                revised_prompt=revised_prompt,
            )
        except Exception as e:
            logger.error(f"genimg error: {e}")
            raise