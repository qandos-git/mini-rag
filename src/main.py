from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase 

from helpers.config import get_settings
from routes import base, data, nlp
from stores.llm.LLMPoviderFactory import LLMProviderFactory

from stores.vectordb.VectorDBProviderFactory import VectorDBProviderFactory

from stores.llm.templates.template_parser import TemplateParser


app = FastAPI()

async def startup_span():
    
    settings = get_settings()
    app.mongo_conn = AsyncIOMotorClient(settings.MONGODB_URL)
    app.db_client = app.mongo_conn[settings.MONGODB_DATABASE]

    llm_provider_factory = LLMProviderFactory(settings)
    vector_db_factory = VectorDBProviderFactory(settings)

    #Generation client
    app.generation_client = llm_provider_factory.create(provider=settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(model_id=settings.GENERATION_MODEL_ID)

    #Embedding client
    app.embedding_client = llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(model_id=settings.EMBEDDING_MODEL_ID,
                                            embedding_size=settings.EMBEDDING_MODEL_SIZE)

    #Vector DB client
    app.vectordb_client = vector_db_factory.create(provider=settings.VECTOR_DB_BACKEND)
    app.vectordb_client.connect()

    app.template_parser = TemplateParser(
            language=settings.PRIMARY_LANG,
            default_language=settings.DEFAULT_LANG,
        )

async def shutdown_span():
    app.mongo_conn.close()


#app.router.lifespan.on_startup.append(startup_span)
#app.router.lifespan.on_shutdown.append(shutdown_span)

app.on_event("startup")(startup_span)
app.on_event("shutdown")(shutdown_span)

# Include the router
app.include_router(base.base_router) # base (module name), base_router (object name in that module)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)