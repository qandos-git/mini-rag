from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv(".env")

from routes import base

app = FastAPI()

# Include the router
app.include_router(base.base_router) # base (module name), base_router (object name in that module)