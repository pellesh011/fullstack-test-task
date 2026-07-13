from src.domain.entities.file import File
from src.infrastructure.database.models import File as FileModel

from .base import Mapper


class FileMapper(Mapper[File, FileModel]):
    def to_entity(
        self,
        model: FileModel,
    ) -> File:
        return File(
            id=model.id,
            title=model.title,
            original_name=model.original_name,
            stored_name=model.stored_name,
            mime_type=model.mime_type,
            original_mime_type=model.original_mime_type,
            size=model.size,
            status=model.status,
            metadata=model.metadata_json,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def to_model(
        self,
        entity: File,
    ) -> FileModel:
        return FileModel(
            id=entity.id,
            title=entity.title,
            original_name=entity.original_name,
            stored_name=entity.stored_name,
            mime_type=entity.mime_type,
            original_mime_type=entity.original_mime_type,
            size=entity.size,
            status=entity.status,
            metadata_json=entity.metadata,
        )
