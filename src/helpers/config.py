from pydantic_settings import BaseSettings

'''
Settings class inherit BaseSettings, and define the settings (datatypes)

Config is nested class provide the metadata to fill the settings with.
'''


class Settings(BaseSettings):

    APP_NAME: str
    APP_VERSION: str

    FILE_ALLOWED_TYPES: list
    FILE_MAX_SIZE: int

    FILE_DEFAULT_CHUNK_SIZE:int

    MONGODB_URL: str
    MONGODB_DATABASE: str


    class Config:
        env_file = ".env" #predefined with pydantic

def get_settings():
    return Settings()
