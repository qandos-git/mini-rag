
from helpers.config import get_settings, Settings



class BaseDataModel:
    """
    Base class for all data models. This class provides a common interface for all data models.
    It also provides a common way to get the settings for the application.
    """

    def __init__(self, db_client: object):
        self.db_client = db_client
        self.app_settings = get_settings()