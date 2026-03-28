from api.routes.artifacts import BulkDeleteRequest


def test_bulk_delete_request():
    req = BulkDeleteRequest(artifact_ids=["1", "2"])
    assert len(req.artifact_ids) == 2
