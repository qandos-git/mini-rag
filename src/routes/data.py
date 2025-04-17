from fastapi import APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
from helpers.config import get_settings, Settings
from controllers import DataController, ProjectController, ProcessController
from .schemes.data import ProcessRequest
import os
import aiofiles
from models import ResponseSignal, AssetTypes
import logging  
from models.ProjectModel import ProjectModel
from models.db_schemes import DataChunk, Asset
from models.ChunkModel import ChunkModel
from models.AssetModel import AssetModel


logger = logging.getLogger('uvicorn.error')
data_controller = DataController()

data_router = APIRouter(
    prefix="/api/v1/data", 
    tags=["api_v1", "data"],
)


@data_router.post("/upload/{project_id}")
async def upload_data(  request: Request,
                        project_id:str,
                        file:UploadFile,
                        app_settings:Settings = Depends(get_settings)):


    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    is_valid, result_signal  = data_controller.validate_uploaded_file(file=file)

    if not is_valid:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={
                                 "signal" : result_signal
                            })
    
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
    

    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)

    asset_resource = Asset(
        asset_project_id=project.id,
        asset_type = AssetTypes.FILE.value,
        asset_name=file_id,
        asset_size=os.path.getsize(file_path)

    )

    asset_record = await asset_model.create_asset(asset=asset_resource)

    return JSONResponse(
        content={
            "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
            "file_id": str(asset_record.id),
                            })


@data_router.post("/process/{project_id}")
async def process_endpoint(request:Request,project_id:str, process_request:ProcessRequest):
    

    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    asset_model = await AssetModel.create_instance(
            db_client=request.app.db_client
        )

    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset

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


    file_chunks_record = [

        DataChunk(
            chunk_text=chunk.page_content,
            chunk_metadata=chunk.metadata,
            chunk_order= i+1,
            chunk_project_id=project.id
        )
        for i, chunk in enumerate(file_chunks)
    ]


    chunk_model  = await ChunkModel.create_instance(
            db_client=request.app.db_client)
    
    deleted_chunks = 0

    if do_reset == 1:
        deleted_chunks = await chunk_model.delete_chunk_by_project_id(project_id=project.id)

    no_records = await chunk_model.insert_many_chunks(chunks=file_chunks_record)
   
    return JSONResponse(
        content={
        "signal" : ResponseSignal.PROCESSING_SUCCESS.value,
        "inserted_chunks": no_records,
        "deleted_chunks": deleted_chunks
        })
 

