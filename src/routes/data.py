from fastapi import APIRouter, Depends, UploadFile, status
from fastapi.responses import JSONResponse
from helpers.config import get_settings, Settings
from controllers import DataController, ProjectController, ProcessController
from .schemes.data import ProcessRequest
import os
import aiofiles
from models import ResponseSignal
import logging  


logger = logging.getLogger('uvicorn.error')
data_controller = DataController()

data_router = APIRouter(
    prefix="/api/v1/data", 
    tags=["api_v1", "data"],
)


@data_router.post("/upload/{project_id}")
async def upload_data(project_id:str,
                      file:UploadFile,
                      app_settings:Settings = Depends(get_settings)):
        
    is_valid, result_signal  = data_controller.validate_uploaded_file(file=file)

    if not is_valid:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={
                                 "signal" : result_signal
                            })
    
    project_dir_path = ProjectController().get_project_path(project_id=project_id)

    file_path, file_id = data_controller.generate_unique_filepath(
        orig_file_name=file.filename,
        project_id=project_id
    )

    try:
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE): #file.read() → Reads a portion of the file asynchronously.
                await f.write(chunk)
    except Exception as e:
        logger.error(f'Error while uploadin file: {e}')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={
                                 "signal" : ResponseSignal.FILE_UPLOAD_FAILED.value
                            })
    
    return JSONResponse(
        content={
            "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
            "file_id": file_id
        }
    )


@data_router.post("/process/{project_id}")
async def process_endpoint(project_id:str, prosess_request:ProcessRequest):
    file_id = prosess_request.file_id
    chunk_size = prosess_request.chunk_size
    overlap_size = prosess_request.overlap_size

    process_controller = ProcessController(project_id=project_id)

    file_content = process_controller.get_file_content(file_id=file_id)

    file_chunks = process_controller.process_file_content(
        file_id=file_id,
        file_content=file_content,
        chunk_size=chunk_size,
        overlap_size=overlap_size
    )

    if file_chunks is None or len(file_chunks) == 0:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={
                                 "signal" : ResponseSignal.PROCESSING_FAILED.value
                            })

    return file_chunks

