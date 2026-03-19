"""Image generation client abstraction with provider implementations."""

from __future__ import annotations

import base64
from abc import ABC, abstractmethod

import httpx
from loguru import logger

_DEFAULT_HOST = "https://api.minimaxi.com"
_IMAGE_GEN_PATH = "/v1/image_generation"

_VALID_ASPECT_RATIOS = frozenset({"1:1", "16:9", "4:3", "3:2", "2:3", "3:4", "9:16"})


class ImageGenerationError(Exception):
    """Raised when an image generation provider returns an error."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class MiniMaxAPIError(ImageGenerationError):
    """Raised when MiniMax returns a business-level error (HTTP 200 but base_resp error)."""

    def __init__(self, status_code: int, status_msg: str) -> None:
        self.status_code = status_code
        self.status_msg = status_msg
        super().__init__(f"MiniMax error {status_code}: {status_msg}")


class ImageGenerationClient(ABC):
    """Abstract interface for image generation providers."""

    @abstractmethod
    async def generate(self, prompt: str, aspect_ratio: str = "1:1") -> list[bytes]:
        """Generate images from a text prompt.

        Args:
            prompt: Text description of the image to generate.
            aspect_ratio: Desired aspect ratio (provider-specific valid values).

        Returns:
            List of image bytes (one per generated image).

        Raises:
            ImageGenerationError: If the provider returns an error.
        """

    @property
    @abstractmethod
    def valid_aspect_ratios(self) -> frozenset[str]:
        """Return the set of valid aspect ratios for this provider."""


class MiniMaxImageClient(ImageGenerationClient):
    """MiniMax image-01 API client."""

    def __init__(
        self,
        api_key: str,
        api_host: str = _DEFAULT_HOST,
    ) -> None:
        if not api_key:
            raise ValueError("MiniMax API key must not be empty")
        self._api_key = api_key
        self._api_url = api_host.rstrip("/") + _IMAGE_GEN_PATH

    @property
    def valid_aspect_ratios(self) -> frozenset[str]:
        return _VALID_ASPECT_RATIOS

    async def generate(self, prompt: str, aspect_ratio: str = "1:1") -> list[bytes]:
        """Call MiniMax image generation API and return decoded image bytes.

        Raises:
            MiniMaxAPIError: If the API returns a business-level error.
            ImageGenerationError: For HTTP or connection errors.
        """
        if aspect_ratio not in _VALID_ASPECT_RATIOS:
            raise ImageGenerationError(
                f"Invalid aspect_ratio '{aspect_ratio}'. "
                f"Must be one of: {', '.join(sorted(_VALID_ASPECT_RATIOS))}"
            )

        try:
            images_b64 = await self._call_api(prompt, aspect_ratio)
        except MiniMaxAPIError:
            raise
        except httpx.HTTPStatusError as exc:
            raise ImageGenerationError(
                f"MiniMax API error (HTTP {exc.response.status_code}): "
                f"{exc.response.text[:200]}"
            ) from exc
        except httpx.HTTPError as exc:
            raise ImageGenerationError(f"MiniMax API request failed: {exc}") from exc

        return [base64.b64decode(img_b64) for img_b64 in images_b64]

    async def _call_api(
        self,
        prompt: str,
        aspect_ratio: str,
    ) -> list[str]:
        """Call MiniMax image generation API and return base64-encoded images."""
        async with httpx.AsyncClient(timeout=120.0, trust_env=False) as client:
            response = await client.post(
                self._api_url,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "image-01",
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "response_format": "base64",
                },
            )
            response.raise_for_status()

        body = response.json()

        base_resp = body.get("base_resp", {})
        resp_code = base_resp.get("status_code", 0)
        if resp_code != 0:
            raise MiniMaxAPIError(
                status_code=resp_code,
                status_msg=base_resp.get("status_msg", "unknown error"),
            )

        data = body.get("data", {})
        if isinstance(data, dict):
            return data.get("image_base64", [])

        logger.warning(
            "MiniMax API unexpected response structure: {}",
            list(body.keys()),
        )
        return []
