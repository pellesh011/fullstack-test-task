from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.schemas import AlertItem, FileItem, FileUpdate, ScanResultItem


class TestFileItem:
    def test_valid(self):
        now = datetime.now(timezone.utc)
        item = FileItem(
            id="test-id",
            title="test",
            original_name="test.txt",
            mime_type="text/plain",
            size=100,
            processing_status="uploaded",
            scan_status=None,
            metadata_json=None,
            requires_attention=False,
            created_at=now,
            updated_at=now,
        )
        assert item.id == "test-id"
        assert item.title == "test"

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            FileItem()

    def test_from_attributes_config(self):
        assert FileItem.model_config.get("from_attributes") is True


class TestFileUpdate:
    def test_valid(self):
        update = FileUpdate(title="new title")
        assert update.title == "new title"

    def test_empty_title(self):
        update = FileUpdate(title="")
        assert update.title == ""

    def test_missing_title(self):
        with pytest.raises(ValidationError):
            FileUpdate()


class TestAlertItem:
    def test_valid(self):
        now = datetime.now(timezone.utc)
        alert = AlertItem(
            id=1,
            file_id="file-id",
            level="info",
            message="test message",
            created_at=now,
        )
        assert alert.id == 1
        assert alert.level == "info"

    def test_from_attributes_config(self):
        assert AlertItem.model_config.get("from_attributes") is True

    def test_invalid_level_type(self):
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            AlertItem(
                id=1,
                file_id="file-id",
                level=123,
                message="test",
                created_at=now,
            )


class TestScanResultItem:
    def test_valid(self):
        now = datetime.now(timezone.utc)
        item = ScanResultItem(
            id=1,
            file_id="file-id",
            check_name="basic_scan",
            status="clean",
            message="no threats found",
            created_at=now,
        )
        assert item.id == 1
        assert item.check_name == "basic_scan"
        assert item.status == "clean"

    def test_nullable_message(self):
        now = datetime.now(timezone.utc)
        item = ScanResultItem(
            id=2,
            file_id="file-id",
            check_name="suspicious_extension",
            status="suspicious",
            message=None,
            created_at=now,
        )
        assert item.message is None

    def test_from_attributes_config(self):
        assert ScanResultItem.model_config.get("from_attributes") is True
