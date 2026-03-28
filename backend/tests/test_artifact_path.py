from datetime import datetime
import uuid
from agent.state.schemas import ArtifactRecord


def test_artifact_record_has_file_path():
    record = ArtifactRecord(
        id="test-id",
        conversation_id=uuid.uuid4(),
        storage_key="test-key",
        original_name="test.txt",
        content_type="text/plain",
        size=100,
        created_at=datetime.now(),
        file_path="folder/test.txt",
    )
    assert record.file_path == "folder/test.txt"
