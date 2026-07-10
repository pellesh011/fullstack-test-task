from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse

from src.application.services.alert_service import AlertService
from src.application.services.file_service import FileService
from src.schemas import AlertItem, FileItem, FileUpdate, ScanResultItem
from src.presentation.dependencies import (
    get_alert_service,
    get_file_service,
)
from src.infrastructure.repositories.scan_result_repository import (
    SQLScanResultRepository,
)
from src.presentation.dependencies import get_scan_result_repo

router = APIRouter()


@router.get("/files", response_model=list[FileItem])
async def list_files_view(
    file_service: FileService = Depends(get_file_service),
):
    return await file_service.list_files()


@router.get("/alerts", response_model=list[AlertItem])
async def list_alerts_view(
    alert_service: AlertService = Depends(get_alert_service),
):
    return await alert_service.list_alerts()


@router.post("/files", response_model=FileItem, status_code=201)
async def create_file_view(
    title: str = Form(...),
    file: UploadFile = File(...),
    file_service: FileService = Depends(get_file_service),
):
    file_item = await file_service.create_file(title=title, upload_file=file)
    return file_item


@router.get("/files/{file_id}", response_model=FileItem)
async def get_file_view(
    file_id: str,
    file_service: FileService = Depends(get_file_service),
):
    return await file_service.get_file(file_id)


@router.patch("/files/{file_id}", response_model=FileItem)
async def update_file_view(
    file_id: str,
    payload: FileUpdate,
    file_service: FileService = Depends(get_file_service),
):
    return await file_service.update_file(file_id=file_id, title=payload.title)


@router.get("/files/{file_id}/download")
async def download_file(
    file_id: str,
    file_service: FileService = Depends(get_file_service),
):
    file_item = await file_service.get_file(file_id)
    stored_path = file_service.get_storage_path(file_item)
    return FileResponse(
        path=stored_path,
        media_type=file_item.mime_type,
        filename=file_item.original_name,
    )


@router.get("/files/{file_id}/scan-results", response_model=list[ScanResultItem])
async def list_scan_results_view(
    file_id: str,
    file_service: FileService = Depends(get_file_service),
    scan_result_repo: SQLScanResultRepository = Depends(get_scan_result_repo),
):
    await file_service.get_file(file_id)
    return list(await scan_result_repo.list_for_file(file_id))


@router.delete("/files/{file_id}", status_code=204)
async def delete_file_view(
    file_id: str,
    file_service: FileService = Depends(get_file_service),
):
    await file_service.delete_file(file_id)
