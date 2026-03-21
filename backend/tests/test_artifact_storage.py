"""Tests for artifact storage backends and ArtifactManager integration."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.artifacts.manager import ArtifactManager
from agent.artifacts.storage import (
    LocalStorageBackend,
    R2StorageBackend,
    create_storage_backend,
)


# ---------------------------------------------------------------------------
# LocalStorageBackend
# ---------------------------------------------------------------------------


class TestLocalStorageBackend:
    """Tests for the local filesystem storage backend."""

    @pytest.fixture()
    def backend(self, tmp_path: os.PathLike) -> LocalStorageBackend:
        return LocalStorageBackend(storage_dir=str(tmp_path))

    async def test_save_creates_file(
        self, backend: LocalStorageBackend, tmp_path: os.PathLike
    ) -> None:
        key = await backend.save("test.png", b"image-data", "image/png")
        assert key == "test.png"
        assert (tmp_path / "test.png").read_bytes() == b"image-data"

    async def test_exists_returns_true_for_saved_file(
        self, backend: LocalStorageBackend
    ) -> None:
        await backend.save("file.txt", b"hello", "text/plain")
        assert await backend.exists("file.txt") is True

    async def test_exists_returns_false_for_missing(
        self, backend: LocalStorageBackend
    ) -> None:
        assert await backend.exists("nope.txt") is False

    async def test_delete_removes_file(
        self, backend: LocalStorageBackend, tmp_path: os.PathLike
    ) -> None:
        await backend.save("del.txt", b"data", "text/plain")
        assert (tmp_path / "del.txt").exists()
        await backend.delete("del.txt")
        assert not (tmp_path / "del.txt").exists()

    async def test_delete_no_error_for_missing(
        self, backend: LocalStorageBackend
    ) -> None:
        # Should not raise
        await backend.delete("missing.txt")

    async def test_get_url_returns_local_path(
        self, backend: LocalStorageBackend, tmp_path: os.PathLike
    ) -> None:
        await backend.save("photo.png", b"img", "image/png")
        url = await backend.get_url("photo.png", "image/png", "photo.png")
        assert url == str(tmp_path / "photo.png")

    async def test_save_blocks_path_traversal(
        self, backend: LocalStorageBackend
    ) -> None:
        with pytest.raises(ValueError, match="traversal"):
            await backend.save("../escape.txt", b"bad", "text/plain")

    async def test_get_url_blocks_path_traversal(
        self, backend: LocalStorageBackend
    ) -> None:
        with pytest.raises(ValueError, match="escapes"):
            await backend.get_url("../escape.txt", "text/plain", "escape.txt")


# ---------------------------------------------------------------------------
# R2StorageBackend (mocked boto3)
# ---------------------------------------------------------------------------


class TestR2StorageBackend:
    """Tests for the R2 storage backend with mocked boto3."""

    @pytest.fixture()
    def mock_client(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture()
    def backend(self, mock_client: MagicMock) -> R2StorageBackend:
        with patch("agent.artifacts.storage.boto3") as mock_boto3:
            mock_boto3.client.return_value = mock_client
            return R2StorageBackend(
                account_id="test-account",
                access_key_id="test-key",
                secret_access_key="test-secret",
                bucket_name="test-bucket",
            )

    @pytest.fixture()
    def backend_with_public_url(self, mock_client: MagicMock) -> R2StorageBackend:
        with patch("agent.artifacts.storage.boto3") as mock_boto3:
            mock_boto3.client.return_value = mock_client
            return R2StorageBackend(
                account_id="test-account",
                access_key_id="test-key",
                secret_access_key="test-secret",
                bucket_name="test-bucket",
                public_url="https://cdn.example.com",
            )

    async def test_save_calls_put_object(
        self, backend: R2StorageBackend, mock_client: MagicMock
    ) -> None:
        await backend.save("img/photo.png", b"image-data", "image/png")
        mock_client.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="img/photo.png",
            Body=b"image-data",
            ContentType="image/png",
        )

    async def test_get_url_returns_presigned_url(
        self, backend: R2StorageBackend, mock_client: MagicMock
    ) -> None:
        mock_client.generate_presigned_url.return_value = (
            "https://test-account.r2.cloudflarestorage.com/signed"
        )
        url = await backend.get_url("photo.png", "image/png", "photo.png")
        assert "signed" in url
        mock_client.generate_presigned_url.assert_called_once()
        call_args = mock_client.generate_presigned_url.call_args
        assert call_args[0][0] == "get_object"
        assert call_args[1]["Params"]["Bucket"] == "test-bucket"
        assert call_args[1]["Params"]["Key"] == "photo.png"

    async def test_get_url_returns_public_url_when_configured(
        self, backend_with_public_url: R2StorageBackend, mock_client: MagicMock
    ) -> None:
        url = await backend_with_public_url.get_url(
            "photo.png", "image/png", "photo.png"
        )
        assert url == "https://cdn.example.com/photo.png"
        mock_client.generate_presigned_url.assert_not_called()

    async def test_delete_calls_delete_object(
        self, backend: R2StorageBackend, mock_client: MagicMock
    ) -> None:
        await backend.delete("photo.png")
        mock_client.delete_object.assert_called_once_with(
            Bucket="test-bucket", Key="photo.png"
        )

    async def test_exists_returns_true(
        self, backend: R2StorageBackend, mock_client: MagicMock
    ) -> None:
        assert await backend.exists("photo.png") is True
        mock_client.head_object.assert_called_once()

    async def test_exists_returns_false_on_error(
        self, backend: R2StorageBackend, mock_client: MagicMock
    ) -> None:
        mock_client.head_object.side_effect = mock_client.exceptions.ClientError = type(
            "ClientError", (Exception,), {}
        )
        assert await backend.exists("missing.png") is False


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------


class TestCreateStorageBackend:
    """Tests for the create_storage_backend factory."""

    def test_returns_local_when_provider_is_local(self) -> None:
        settings = MagicMock(STORAGE_PROVIDER="local", STORAGE_DIR="/tmp/arts")
        backend = create_storage_backend(settings)
        assert isinstance(backend, LocalStorageBackend)
        assert backend._storage_dir == "/tmp/arts"

    def test_returns_local_by_default(self) -> None:
        settings = MagicMock(spec=[])  # no attributes
        backend = create_storage_backend(settings)
        assert isinstance(backend, LocalStorageBackend)

    def test_raises_when_r2_missing_credentials(self) -> None:
        settings = MagicMock(
            STORAGE_PROVIDER="r2",
            R2_ACCOUNT_ID="acct",
            R2_ACCESS_KEY_ID="key",
            R2_SECRET_ACCESS_KEY="",  # Missing
            R2_BUCKET_NAME="bucket",
        )
        with pytest.raises(RuntimeError, match="R2_SECRET_ACCESS_KEY"):
            create_storage_backend(settings)

    @patch("agent.artifacts.storage.boto3")
    def test_returns_r2_when_fully_configured(self, _mock_boto3: MagicMock) -> None:
        settings = MagicMock(
            STORAGE_PROVIDER="r2",
            R2_ACCOUNT_ID="acct",
            R2_ACCESS_KEY_ID="key",
            R2_SECRET_ACCESS_KEY="secret",
            R2_BUCKET_NAME="bucket",
            R2_PUBLIC_URL="",
        )
        backend = create_storage_backend(settings)
        assert isinstance(backend, R2StorageBackend)

    def test_raises_for_unknown_provider(self) -> None:
        settings = MagicMock(STORAGE_PROVIDER="s3")
        with pytest.raises(ValueError, match="Unknown STORAGE_PROVIDER"):
            create_storage_backend(settings)


# ---------------------------------------------------------------------------
# ArtifactManager with storage backend
# ---------------------------------------------------------------------------


class TestArtifactManagerWithBackend:
    """Tests for ArtifactManager delegating to a storage backend."""

    @pytest.fixture()
    def mock_backend(self) -> MagicMock:
        backend = MagicMock()
        backend.save = AsyncMock(return_value="saved-key")
        backend.get_url = AsyncMock(return_value="https://example.com/file.txt")
        backend.delete = AsyncMock()
        backend.exists = AsyncMock(return_value=True)
        return backend

    @pytest.fixture()
    def manager(self, mock_backend: MagicMock) -> ArtifactManager:
        return ArtifactManager(storage_backend=mock_backend)

    async def test_register_delegates_to_backend(
        self, manager: ArtifactManager, mock_backend: MagicMock
    ) -> None:
        artifact = await manager.register_local_artifact(
            data=b"hello", filename="test.txt"
        )
        mock_backend.save.assert_called_once()
        call_args = mock_backend.save.call_args[0]
        assert call_args[0].endswith(".txt")  # key has extension
        assert call_args[1] == b"hello"  # data
        assert call_args[2] == "text/plain"  # content_type
        assert artifact.original_name == "test.txt"
        assert artifact.size == 5

    async def test_get_url_delegates_to_backend(
        self, manager: ArtifactManager, mock_backend: MagicMock
    ) -> None:
        artifact = await manager.register_local_artifact(
            data=b"hello", filename="test.txt"
        )
        url = await manager.get_url(artifact)
        assert url == "https://example.com/file.txt"

    async def test_get_path_raises_for_non_local_backend(
        self, manager: ArtifactManager
    ) -> None:
        artifact = await manager.register_local_artifact(
            data=b"hello", filename="test.txt"
        )
        with pytest.raises(RuntimeError, match="LocalStorageBackend"):
            manager.get_path(artifact)

    async def test_get_path_works_with_local_backend(
        self, tmp_path: os.PathLike
    ) -> None:
        local_backend = LocalStorageBackend(storage_dir=str(tmp_path))
        mgr = ArtifactManager(storage_dir=str(tmp_path), storage_backend=local_backend)
        artifact = await mgr.register_local_artifact(data=b"hello", filename="test.txt")
        path = mgr.get_path(artifact)
        assert os.path.isfile(path)
        assert path.endswith(".txt")
