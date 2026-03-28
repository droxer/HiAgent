from agent.artifacts.manager import Artifact


def test_artifact_has_file_path():
    artifact = Artifact(
        id="test-id",
        path="test-path",
        original_name="test.txt",
        content_type="text/plain",
        size=100,
        file_path="folder/test.txt",
    )
    assert artifact.file_path == "folder/test.txt"
