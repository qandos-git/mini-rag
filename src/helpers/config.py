from pydantic_settings import BaseSettings, SettingsConfigDict

'''
Settings class inherit BaseSettings, and define the settings (datatypes)

Config is nested class provide the metadata to fill the settings with.
'''


class Settings(BaseSettings):

    APP_NAME: str
    APP_VERSION: str
    OPENAI_API_KEY: str

    class Config:
        env_file = ".env" #predefined with pydantic

def get_settings():
    return Settings()
