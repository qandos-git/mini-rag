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
    
    GENERATION_BACKEND: str
    EMBEDDING_BACKEND: str

    OPENAI_API_KEY: str = None
    OPENAI_API_URL: str = None
    COHERE_API_KEY: str = None

    GENERATION_MODEL_ID: str = None
    EMBEDDING_MODEL_ID: str = None
    EMBEDDING_MODEL_SIZE: int = None
    INPUT_DAFAULT_MAX_CHARACTERS: int = None
    GENERATION_DAFAULT_MAX_TOKENS: int = None
    GENERATION_DAFAULT_TEMPERATURE: float = None

    VECTOR_DB_BACKEND: str
    VECTOR_DB_PATH: str
    VECTOR_DB_DISTANCE_METHOD: str

    PRIMARY_LANG : str
    DEFAULT_LANG : str


    class Config:
        env_file = ".env" #predefined with pydantic

def get_settings():
    return Settings()
