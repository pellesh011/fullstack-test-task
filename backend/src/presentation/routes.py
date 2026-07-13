from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from src.application.services.file_service import FileService
from src.domain.exceptions import (
    DomainException,
    FileEmptyError,
    FileNotFoundError,
    StoredFileNotFoundError,
)
from src.schemas import FileItem, FileUpdate, TaskExecutionIssue
from src.presentation.dependencies import get_file_service, get_task_execution_repo
from src.domain.interfaces.repositories import TaskExecutionRepository

router = APIRouter()


@router.get("/files", response_model=list[FileItem])
async def list_files_view(
    file_service: FileService = Depends(get_file_service),
):
    return await file_service.list_files()


@router.post("/files", response_model=FileItem, status_code=201)
async def create_file_view(
    title: str = Form(...),
    file: UploadFile = File(...),
    file_service: FileService = Depends(get_file_service),
):
    try:
        file_item = await file_service.create_file(title=title, upload_file=file)
        return file_item
    except FileEmptyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/files/{file_id}", response_model=FileItem)
async def get_file_view(
    file_id: str,
    file_service: FileService = Depends(get_file_service),
):
    try:
        return await file_service.get_file(file_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/files/{file_id}", response_model=FileItem)
async def update_file_view(
    file_id: str,
    payload: FileUpdate,
    file_service: FileService = Depends(get_file_service),
):
    try:
        return await file_service.update_file(file_id=file_id, title=payload.title)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/files/{file_id}/download")
async def download_file(
    file_id: str,
    file_service: FileService = Depends(get_file_service),
):
    try:
        file_item = await file_service.get_file(file_id)
        stored_path = file_service.get_storage_path(file_item)
        return FileResponse(
            path=stored_path,
            media_type=file_item.mime_type,
            filename=file_item.original_name,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except StoredFileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/files/{file_id}", status_code=204)
async def delete_file_view(
    file_id: str,
    file_service: FileService = Depends(get_file_service),
):
    try:
        await file_service.delete_file(file_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/task-executions/issues", response_model=list[TaskExecutionIssue])
async def list_task_execution_issues(
    repo: TaskExecutionRepository = Depends(get_task_execution_repo),
):
    return await repo.list_non_success()
