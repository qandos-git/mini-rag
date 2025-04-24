from .VectorDBEnums import VectorDBEnums
from .providers import QdrantDBProvider
from controllers.BaseController import BaseController

class VectorDBProviderFactory:
    def __init__(self, config: dict):
        self.config = config
        self.base_controllere = BaseController()


    def create(self, provider: str):
        if provider == VectorDBEnums.QDRANT.value:
            db_path = self.base_controllere.get_database_path(self.config.VECTOR_DB_BACKEND)
            return QdrantDBProvider(
                db_path = db_path,
                distance_method= self.config.VECTOR_DB_DISTANCE_METHOD
            )
        return None