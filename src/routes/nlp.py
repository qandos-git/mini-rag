from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse
from controllers import NLPController
from .schemes.nlp import PushRequest, SearchRequest
import logging  
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from models.enums.ResponseEnums import ResponseSignal


logger = logging.getLogger('uvicorn.error')

nlp_router = APIRouter(
    prefix="/api/v1/nlp", 
    tags=["api_v1", "nlp"],
)

@nlp_router.post("/index/push/{project_id}")
async def index_project(request: Request, project_id:str, push_request: PushRequest):

    #CollectionsDB Object model
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client)
    
    chunk_model = await ChunkModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id)
    
    #Route controller
    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        embedding_client=request.app.embedding_client,
        generation_client=request.app.generation_client,
        project=project)
    
    #Method variable
    has_records = True
    page_no = 1
    idx = 0
    inserted_items_count = 0

    while has_records:
        page_chunks = await chunk_model.get_all_project_chunks(projec_id=project.id,
                                           page_no=page_no)
        if not page_chunks:
            has_records = False
            break
        
        chunks_ids =  list(range(idx, idx + len(page_chunks)))
    
        is_inserted = nlp_controller.index_into_vector_db(
            chunks=page_chunks,
            chunks_ids=chunks_ids, 
            do_reset=push_request.do_reset)
       
        if not is_inserted:
                return JSONResponse(
                     status_code=status.HTTP_400_BAD_REQUEST,
                     content={
                    "signal": ResponseSignal.INSERT_INTO_VECTORDB_ERROR.value
                    }
                )
        
        idx += len(page_chunks)
        inserted_items_count += len(page_chunks)
        page_no +=1

    
    return JSONResponse(
        content={
            "signal": ResponseSignal.INSERT_INTO_VECTORDB_SUCCESS.value,
            "inserted_items_count": inserted_items_count
        }
    )


@nlp_router.get("/index/info/{project_id}")
async def get_project_index_info(request: Request, project_id:str):
        
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client)
    
    project = await project_model.get_project_or_create_one(
        project_id=project_id)
    
    #Route controller
    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        embedding_client=request.app.embedding_client,
        generation_client=request.app.generation_client,
        project=project)
    
    collection_info = nlp_controller.get_vector_db_collection_info()
    

    return JSONResponse(
        content={
            "signal": ResponseSignal.VECTORDB_COLLECTION_RETRIEVED.value,
            "collection_info": collection_info
        }
    )

@nlp_router.post("/index/search/{project_id}")
async def search_index(request: Request, project_id:str, search_request: SearchRequest):
    
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client)
    
    project = await project_model.get_project_or_create_one(
        project_id=project_id)
    
    #Route controller
    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        embedding_client=request.app.embedding_client,
        generation_client=request.app.generation_client,
        project=project)

    results = nlp_controller.search_vector_db_collection(
        text=search_request.text,
        limit=search_request.limit 
        )

    if not results:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.VECTORDB_SEARCH_ERROR.value,
            }
        )  
    
    return JSONResponse(
        content={
            "signal": ResponseSignal.VECTORDB_SEARCH_SUCCESS.value,
            "results": [result.dict() for result in results]
        }
    )

@nlp_router.post("/index/answer/{project_id}")
async def answer_rag(request: Request, project_id: str, search_request: SearchRequest):
    
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        project=project
    )

    answer, full_prompt, chat_history = nlp_controller.answer_rag_question(
        query=search_request.text,
        template_parser=request.app.template_parser,
        limit=search_request.limit,
    )

    if not answer:
        return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.RAG_ANSWER_ERROR.value
                }
        )
    
    return JSONResponse(
        content={
            "signal": ResponseSignal.RAG_ANSWER_SUCCESS.value,
            "answer": answer,
            "full_prompt": full_prompt,
            "chat_history": chat_history
        }
    )