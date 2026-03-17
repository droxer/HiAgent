"""Tests for the ImageGen tool."""

from __future__ import annotations

import base64
from unittest.mock import patch

import httpx
import pytest

from agent.artifacts.manager import ArtifactManager
from agent.tools.base import ExecutionContext
from agent.tools.local.image_gen import ImageGen
from api.events import EventEmitter, EventType


@pytest.fixture
def artifact_manager(tmp_path):
    return ArtifactManager(storage_dir=str(tmp_path / "artifacts"))


@pytest.fixture
def event_emitter():
    return EventEmitter()


@pytest.fixture
def tool(artifact_manager, event_emitter):
    return ImageGen(
        api_key="test-key",
        artifact_manager=artifact_manager,
        event_emitter=event_emitter,
    )


def test_definition(tool):
    defn = tool.definition()
    assert defn.name == "image_generate"
    assert defn.execution_context == ExecutionContext.LOCAL
    assert "prompt" in defn.input_schema["required"]
    assert "aspect_ratio" in defn.input_schema["properties"]


@pytest.mark.asyncio
async def test_empty_prompt_fails(tool):
    result = await tool.execute(prompt="")
    assert not result.success
    assert "empty" in result.error.lower()


@pytest.mark.asyncio
async def test_whitespace_prompt_fails(tool):
    result = await tool.execute(prompt="   ")
    assert not result.success


@pytest.mark.asyncio
async def test_invalid_aspect_ratio(tool):
    result = await tool.execute(prompt="a cat", aspect_ratio="5:3")
    assert not result.success
    assert "aspect_ratio" in result.error.lower()


@pytest.mark.asyncio
async def test_successful_generation(tool, artifact_manager):
    """Mock the MiniMax API to return a base64 JPEG and verify artifact creation."""
    jpeg_bytes = b"\xff\xd8\xff\xe0fake-jpeg-data"
    b64_data = base64.b64encode(jpeg_bytes).decode()

    mock_response = httpx.Response(
        status_code=200,
        json={"data": {"image_base64": [b64_data]}},
        request=httpx.Request("POST", "https://api.minimax.io/v1/image_generation"),
    )

    emitted_events: list[tuple] = []
    original_emit = tool._event_emitter.emit

    async def capture_emit(event_type, data, **kw):
        emitted_events.append((event_type, data))
        await original_emit(event_type, data, **kw)

    tool._event_emitter.emit = capture_emit

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        result = await tool.execute(prompt="a cute cat")

    assert result.success
    assert "1 image" in result.output
    assert result.metadata["count"] == 1
    assert len(result.metadata["artifact_ids"]) == 1

    # Verify artifact was registered
    artifact_id = result.metadata["artifact_ids"][0]
    artifact = artifact_manager.get_artifact(artifact_id)
    assert artifact is not None
    assert artifact.content_type == "image/jpeg"
    assert artifact.size == len(jpeg_bytes)

    # Verify ARTIFACT_CREATED event was emitted
    artifact_events = [
        (t, d) for t, d in emitted_events if t == EventType.ARTIFACT_CREATED
    ]
    assert len(artifact_events) == 1
    assert artifact_events[0][1]["artifact_id"] == artifact_id


@pytest.mark.asyncio
async def test_multiple_images(tool, artifact_manager):
    """Verify that multiple images in response create multiple artifacts."""
    jpeg_bytes = b"\xff\xd8\xff\xe0fake"
    b64_data = base64.b64encode(jpeg_bytes).decode()

    mock_response = httpx.Response(
        status_code=200,
        json={"data": {"image_base64": [b64_data, b64_data, b64_data]}},
        request=httpx.Request("POST", "https://api.minimax.io/v1/image_generation"),
    )

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        result = await tool.execute(prompt="three cats")

    assert result.success
    assert result.metadata["count"] == 3
    assert len(result.metadata["artifact_ids"]) == 3

    # All artifacts should be distinct
    ids = result.metadata["artifact_ids"]
    assert len(set(ids)) == 3


@pytest.mark.asyncio
async def test_empty_response_fails(tool):
    """Verify that an empty image list returns a failure."""
    mock_response = httpx.Response(
        status_code=200,
        json={"data": {"image_base64": []}},
        request=httpx.Request("POST", "https://api.minimax.io/v1/image_generation"),
    )

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        result = await tool.execute(prompt="a cat")

    assert not result.success
    assert "no images" in result.error.lower()


@pytest.mark.asyncio
async def test_api_http_error(tool):
    """Verify that HTTP errors from the API are handled gracefully."""
    mock_response = httpx.Response(
        status_code=429,
        text="Rate limit exceeded",
        request=httpx.Request("POST", "https://api.minimax.io/v1/image_generation"),
    )

    with patch(
        "httpx.AsyncClient.post",
        side_effect=httpx.HTTPStatusError(
            "rate limited", request=mock_response.request, response=mock_response
        ),
    ):
        result = await tool.execute(prompt="a cat")

    assert not result.success
    assert "429" in result.error


@pytest.mark.asyncio
async def test_api_connection_error(tool):
    """Verify that connection errors are handled gracefully."""
    with patch(
        "httpx.AsyncClient.post",
        side_effect=httpx.ConnectError("connection refused"),
    ):
        result = await tool.execute(prompt="a cat")

    assert not result.success
    assert "failed" in result.error.lower()


@pytest.mark.asyncio
async def test_api_business_error(tool):
    """Verify that MiniMax base_resp errors (HTTP 200 but error body) are handled."""
    mock_response = httpx.Response(
        status_code=200,
        json={"base_resp": {"status_code": 2049, "status_msg": "invalid api key"}},
        request=httpx.Request("POST", "https://api.minimax.io/v1/image_generation"),
    )

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        result = await tool.execute(prompt="a cat")

    assert not result.success
    assert "invalid api key" in result.error.lower()
    assert "2049" in result.error


def test_empty_api_key_raises():
    """Constructor should reject empty API key."""
    with pytest.raises(ValueError, match="must not be empty"):
        ImageGen(
            api_key="",
            artifact_manager=ArtifactManager(),
            event_emitter=EventEmitter(),
        )
