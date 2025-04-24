from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMethodEnums
from typing import List


from qdrant_client import models, QdrantClient
import logging


class QdrantDBProvider(VectorDBInterface):
    def __init__(self, db_path: str, distance_method: str):
        self.db_path= db_path
        self.client = None

        self.distance_method = DistanceMethodEnums.COSINE.value
        if distance_method == DistanceMethodEnums.DOT.value:
            self.distance_method = DistanceMethodEnums.DOT.value


        self.logger = logging.getLogger(__name__)


    def connect(self):
        self.client =  QdrantClient(path=self.db_path)

    def disconnect(self):
        self.client = None

    def is_collection_existed(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name=collection_name)

    def list_all_collections(self) -> List:
        return self.client.get_collections()

    def get_collection_info(self, collection_name: str) -> dict:
        return self.client.get_collection(collection_name=collection_name)
    

    def delete_collection(self, collection_name: str):
        if self.is_collection_existed(collection_name=collection_name):
            return self.client.delete_collection(collection_name="{collection_name}")
        self.logger.error("Collection {collection_name} not exists")
        return None
 

    def create_collection(self, collection_name: str, 
                                embedding_size: int,
                                do_reset: bool = False):
        if do_reset:
            self.delete_collection(collection_name=collection_name)
        if not self.is_collection_existed(collection_name=collection_name):
            _ = self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=embedding_size, distance=self.distance_method),
                )
            return True
        return False


    def insert_one(self, collection_name: str, text: str, vector: list,
                         metadata: dict = None, 
                         record_id: str = None):
        if self.is_collection_existed(collection_name=collection_name):
            try:
                _ = self.client.upload_records(
                    collection_name=collection_name,
                    records=[
                        models.Record(
                            id=[record_id],
                            vector=vector,
                            payload={
                                "text": text, "metadata": metadata
                            }
                        )
                    ]
                )
                return True
            except Exception as e:
                self.logger.error(f"Problem while inseting one record: {e}")
                return False
        
        self.logger.error(f"Can not insert new record to non-existed collection: {collection_name}")
        return False
        
    def insert_many(self, collection_name: str, texts: list, 
                          vectors: list, metadata: list = None, 
                          record_ids: list = None, batch_size: int = 50):
        if self.is_collection_existed(collection_name=collection_name):
            if metadata is None:
                metadata = [None] * len(texts)

            if record_ids is None:
                record_ids = list(range(0, len(texts)))

            for i in range(0, len(texts), batch_size):
                batch_end = i + batch_size
                batch_texts = texts[:batch_end]
                batch_vectors = vectors[:batch_end]
                batch_metadata = metadata[:batch_end]
                batch_record_ids = record_ids[i:batch_end]

                batch_records = [
                    models.Record(
                        id=batch_record_ids[x],
                        vector=batch_vectors[x],
                        payload={
                            "text": batch_texts[x],
                            "metadata": batch_metadata[x]
                            }
                            )
                    for x in range(len(batch_texts))
                ]

                try:
                    _ = self.client.upload_records(
                    collection_name=collection_name,
                    records=batch_records
                    )
                except Exception as e:
                    self.logger.error(f"Error while inserting batch: {e}")
                    return False
                
            return True
        

        self.logger.error(f"Can not insert new records to non-existed collection: {collection_name}")
        return False



    def search_by_vector(self, collection_name: str, vector: list, limit: int = 5):
        return self.client.search(
            collection_name=collection_name,
            query_vector=vector,
            limit=limit
            )





