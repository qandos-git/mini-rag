from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase 

from helpers.config import get_settings
from routes import base, data



app = FastAPI()



@app.on_event("startup")
async def startup_db_client():
    
    settings = get_settings()

    app.mongo_conn = AsyncIOMotorClient(settings.MONGODB_URL)
    app.db_client = app.mongo_conn[settings.MONGODB_DATABASE]

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongo_conn.close()

# Include the router
app.include_router(base.base_router) # base (module name), base_router (object name in that module)
app.include_router(data.data_router)