from .BaseDataModel import BaseDataModel
from .db_schemes import DataChunk
from bson.objectid import ObjectId
from sqlalchemy.future import select
from sqlalchemy import delete

class ChunkModel(BaseDataModel):
    
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)

    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        return instance


    async def create_chunk(self, chunk: DataChunk):
        async with self.db_client() as session:
            async with session.begin():
                session.add(chunk)
            await session.refresh(chunk)
        return chunk
    
    
    async def get_chunk(self, chunk_id: str):
        async with self.db_client() as session:
                query = select(DataChunk).where(
                    DataChunk.chunk_id==chunk_id
                    )
                result = await session.execute(query)
                chunk = result.scalar_one_or_none()
        return chunk


    async def insert_many_chunks(self, chunks: list, batch_size: int=100):
        async with self.db_client() as session:
            async with session.begin():
                for i in range(0, len(chunks), batch_size):
                    batch = chunks[i:i+batch_size]
                    session.add_all(batch)
        return len(chunks)
            

    async def delete_chunk_by_project_id(self, project_id:ObjectId):
        async with self.db_client() as session:
            async with session.begin():
                statement = delete(DataChunk).where(DataChunk.chunk_project_id==project_id)
                result = await session.execute(statement)
        return result.rowcount


    async def get_poject_chunks(self, project_id: ObjectId, page_no: int=1, page_size: int=50):
        async with self.db_client() as session:
            stmt = select(DataChunk).where(DataChunk.chunk_project_id == project_id).offset((page_no - 1) * page_size).limit(page_size)
            result = await session.execute(stmt)
            records = result.scalars().all()
        return records