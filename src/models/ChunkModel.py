from .BaseDataModel import BaseDataModel
from .enums.DataBaseEnum import DataBaseEnum
from .db_schemes import DataChunk
from bson.objectid import ObjectId
from pymongo import InsertOne

class ChunkModel(BaseDataModel):
    
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTION_CHNK_NAME.value]

    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        await instance.init_collection()
        return instance

    async def init_collection(self):
        all_collections = await self.db_client.list_collection_names()
        if self.collection not in all_collections:
            self.collection = self.db_client[DataBaseEnum.COLLECTION_CHNK_NAME.value]
            indexes = DataChunk.get_indexes()
            for index in indexes:
                self.collection.create_index(
                    index["key"],
                    name=index["name"],
                    unique=index["unique"]
                )

    async def create_chunk(self, chunk: DataChunk):
        result = await self.collection.insert_one(chunk.dict(by_alias=True, exclude_unset=True))
        chunk.id = result.inserted_id
        return chunk
    
    async def get_chunk(self, chunk_id: str):
        result = await self.collection.find_one(
            {"_id": ObjectId(chunk_id) } #Search for chunk using chunk_id in ObjectId type which is (db accepted type for _id field in MongoDB database)
        )

        if result is None:
            return None
        
        return DataChunk(**result) #return results as DataChunk object
    

    async def insert_many_chunks(self, chunks: list, batch_size: int = 100):
        for i in range(0, len(chunks), batch_size): #start, stop, step_size
            batch = chunks[i: i+batch_size] #define the batch as part of chunks list

            operations = [
                InsertOne(chunk.dict(by_alias=True, exclude_unset=True))
                for chunk in batch
            ]

            await self.collection.bulk_write(operations)

        return len(chunks)
            

    async def delete_chunk_by_project_id(self, project_id:ObjectId):
        result = await self.collection.delete_many({
            "chunk_project_id": project_id
        })

        return result.deleted_count
    
    async def get_all_project_chunks(self, projec_id:ObjectId,page_no: int=1, page_size: int=50):
        records = await self.collection.find({
            "chunk_project_id":projec_id
        }).skip(
            (page_no-1) * page_size
        ).limit(page_size).to_list(length=None)
        
        return [
            DataChunk(**record)
            for record in records
        ]