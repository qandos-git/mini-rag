from .VectorDBEnums import VectorDBEnums
from .providers import QdrantDBProvider, PGVectorDBProvider
from controllers.BaseController import BaseController
from sqlalchemy.orm import sessionmaker

class VectorDBProviderFactory:
    def __init__(self, config: dict, db_client: sessionmaker = None):
        self.config = config
        self.db_client = db_client
        self.base_controllere = BaseController()
        
    def create(self, provider: str,):
        if provider == VectorDBEnums.QDRANT.value:
            quadrant_db_client = self.base_controllere.get_database_path(self.config.VECTOR_DB_BACKEND)
            return QdrantDBProvider(
                db_path = quadrant_db_client,
                distance_method= self.config.VECTOR_DB_DISTANCE_METHOD,
                default_vector_size = self.config.EMBEDDING_MODEL_SIZE,
                index_threshold = self.config.VECTOR_DB_INDEX_THRESHOLD,
            )  
        if provider == VectorDBEnums.PGVECTOR.value:
            if not self.db_client:
                raise ValueError("Database client is not provided for PgvectorDBProvider")
            return PGVectorDBProvider(
                db_client = self.db_client,
                distance_method= self.config.VECTOR_DB_DISTANCE_METHOD,
                default_vector_size = self.config.EMBEDDING_MODEL_SIZE,
                index_threshold = self.config.VECTOR_DB_INDEX_THRESHOLD,
            )

        return None