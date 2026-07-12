from src.domain.entities.stored_file import StoredFile
from src.infrastructure.database.models import StoredFile as StoredFileModel

from .base import Mapper


class FileMapper(Mapper[StoredFile, StoredFileModel]):
    def to_entity(
        self,
        model: StoredFileModel,
    ) -> StoredFile:
        return StoredFile(
            id=model.id,
            title=model.title,
            original_name=model.original_name,
            stored_name=model.stored_name,
            mime_type=model.mime_type,
            original_mime_type=model.original_mime_type,
            size=model.size,
            processing_status=model.processing_status,
            scan_status=model.scan_status,
            metadata=model.metadata_json,
            requires_attention=model.requires_attention,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def to_model(
        self,
        entity: StoredFile,
    ) -> StoredFileModel:
        return StoredFileModel(
            id=entity.id,
            title=entity.title,
            original_name=entity.original_name,
            stored_name=entity.stored_name,
            mime_type=entity.mime_type,
            original_mime_type=entity.original_mime_type,
            size=entity.size,
            processing_status=entity.processing_status,
            scan_status=entity.scan_status,
            metadata_json=entity.metadata,
            requires_attention=entity.requires_attention,
        )
