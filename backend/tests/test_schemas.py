from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.schemas import FileItem, FileUpdate


class TestFileItem:
    def test_valid(self):
        now = datetime.now(timezone.utc)
        item = FileItem(
            id="test-id",
            title="test",
            original_name="test.txt",
            mime_type="text/plain",
            original_mime_type=None,
            size=100,
            status="new",
            metadata_json=None,
            created_at=now,
            updated_at=now,
        )
        assert item.id == "test-id"
        assert item.title == "test"

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            FileItem(
                title="test",
                original_name="y",
                mime_type="z",
                size=1,
                status="new",
                metadata_json=None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

    def test_from_attributes_config(self):
        assert FileItem.model_config.get("from_attributes") is True


class TestFileUpdate:
    def test_valid(self):
        update = FileUpdate(title="new title")
        assert update.title == "new title"

    def test_missing_title(self):
        with pytest.raises(ValidationError):
            FileUpdate()
