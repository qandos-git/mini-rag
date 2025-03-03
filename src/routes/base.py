'''
This route is used to check if tha app up up or down
''' 
from fastapi import APIRouter
import os


''''
APIRouter is a FastAPI utility that allows you 
to organize your API by defining separate routers
for different parts of your application.
'''

base_router = APIRouter(
    prefix="/api/v1", # This is used to prefix all routes registered under this router.
    tags=["api_v1"], # This helps categorize routes in the API documentation.
)

@base_router.get("/") 
async def welcome():
    app_name = os.getenv('APP_NAME') # Retrieves APP_NAME from environment variables
    app_version = os.getenv('APP_VERSION') # Retrieves APP_VERSION from environment variables.


    return {
        "app_name": app_name,
        "app_version": app_version,
    }