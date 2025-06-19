from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import PgVectorDistanceMethodEnums, PgVectorTableSchemeEnums, PgVectorIndexTypeEnums
from models.db_schemes import RetrievedDocument
from typing import List
import logging
import json

from sqlalchemy.sql import text as sql_text

class PGVectorDBProvider(VectorDBInterface):
    def __init__(self, db_client, 
                 distance_method: str = None,
                 default_vector_size: int = 786,
                 index_threshold:int = 100):

        self.db_client = db_client

        self.distance_method = PgVectorDistanceMethodEnums.COSINE.value
        if distance_method == PgVectorDistanceMethodEnums.DOT.value:
            self.distance_method = PgVectorDistanceMethodEnums.DOT.value

        self.logger = logging.getLogger("uvicorn") #have to change it to __name__ later

        self.default_vector_size = default_vector_size

        self.index_name = lambda collection_name: f'{collection_name}_table_idx'

        self.index_threshold = index_threshold


        
    async def connect(self):
        '''
        Enable PGVector extention in postgres database (required step)
        '''
        async with self.db_client() as session:
            async with session.begin():
                await session.execute(sql_text(
                    "CREATE EXTENSION IF NOT EXISTS vector;"
                ))
            


    def disconnect(self):
        pass

    async def is_collection_existed(self, collection_name: str) -> bool:
        stm = sql_text("""SELECT EXISTS (
                       SELECT FROM pg_tables 
                       WHERE tablename = :collection_name
                       )""")
        async with self.db_client() as session:
            async with session.begin():
                result = await session.execute(stm, {"collection_name": collection_name})
        return result.scalar_one_or_none()


    async def list_all_collections(self) -> List:
        stm = sql_text("SELECT tablename FROM pg_tables WHERE tablename LIKE :prefix;")

        async with self.db_client() as session:
            async with session.begin():
                result = await session.execute(stm, {"prefix":PgVectorTableSchemeEnums._PREFIX.value})
        return result.scalars().all()


    async def get_collection_info(self, collection_name: str) -> dict:
        stm_info = sql_text(f"""
                       SELECT schemaname, tablename, tableowner, tablespace, hasindexes 
                       FROM pg_tables 
                       WHERE tablename = :collection_name
                        """)
        stm_count = sql_text(f"SELECT COUNT(*) FROM {collection_name}")
        
        async with self.db_client() as session:
            async with session.begin():
                table_info = await session.execute(stm_info,{"collection_name": collection_name})                 
                record_count = await session.execute(stm_count) 

        table_data = table_info.fetchone()
        if not table_data:
            return None

                
        return {
            "table_info": {
                "schemaname": table_data[0],
                "tablename": table_data[1],
                "tableowner": table_data[2],
                "tablespace": table_data[3],
                "hasindexes": table_data[4],}
                ,
                "record_count": record_count.scalar_one(),}
                

    async def delete_collection(self, collection_name: str):
        self.logger.info(f"Attempting to delete collection: {collection_name}")
        stm = sql_text(f"DROP TABLE IF EXISTS {collection_name}")
        async with self.db_client() as session:
            async with session.begin():
                await session.execute(stm) 

        self.logger.info(f"Deleting collection: {collection_name}")
        return True
    


    async def is_index_existed(self, collection_name: str) ->bool:
        index_name = self.index_name(collection_name)
        stm = sql_text(f"""
                SELECT 1 
                FROM pg_indexes 
                WHERE tablename = :collection_name
                AND indexname = :index_name
                """)
        async with self.db_client() as session:
            async with session.begin():
                result = await session.execute(stm,
                                               {"collection_name":collection_name,
                                               "index_name":index_name})
        
                return bool(result.scalar_one_or_none())
    
    async def create_vector_index(self, collection_name:str,
                                    index_type: str = PgVectorIndexTypeEnums.HNSW.value):

        if await self.is_index_existed(collection_name=collection_name):
            #self.logger.info("index is already existed, no need to create it")
            return False

        stm_count = sql_text(f"SELECT COUNT(*) FROM {collection_name}")
        async with self.db_client() as session:
            async with session.begin():
                result = await session.execute(stm_count)
                stm_threshold = result.scalar_one()
                if stm_threshold < self.index_threshold:
                    self.logger.warning(f"Can't create index: Number of records in {collection_name} must be >= {self.index_threshold}")
                    self.logger.warning(f"create_vector_index return False as We have {stm_threshold} records in {collection_name}")
                    return False
                
                else:
                    #creating index consume time so track it with logger
                    self.logger.info(f"START: Creating vector index for collection: {collection_name}")
                    index_name = self.index_name(collection_name)
                    stm_index = sql_text(f'CREATE INDEX {index_name} ON {collection_name} '
                                        f'USING {index_type} ({PgVectorTableSchemeEnums.VECTOR.value} {self.distance_method})')
                    
                _ = await session.execute(stm_index)
                
                self.logger.info(f"END: Created index: {index_name} for collection: {collection_name}")
                return True
            


    async def reset_vector_index(self, collection_name: str, 
                                       index_type: str = PgVectorIndexTypeEnums.HNSW.value) -> bool:
        

        '''
        The index clusters get old by time (data increase)
        thus we have to reset the old index so the new index is more effictive
        '''
        if await self.is_collection_existed(collection_name):
            self.logger.info("Can not create new index to non-existed collection")
            return False

        index_name = self.index_name(collection_name)
        async with self.db_client() as session:
            async with session.begin():
                stm = sql_text(f'DROP INDEX IF EXISTS {index_name}')
                await session.execute(stm)
                self.logger.info(f"{index_name} for collection: {collection_name} is dropped to be reset")

        return await self.create_vector_index(collection_name=collection_name, index_type=index_type)


    async def create_collection(self, collection_name: str, 
                                embedding_size: int,
                                do_reset: bool = False):
        if do_reset:
            _ = await self.delete_collection(collection_name=collection_name)
        if not await self.is_collection_existed(collection_name=collection_name):
            self.logger.info(f"Creating collection: {collection_name}")
            
            stm = sql_text(f"""CREATE TABLE {collection_name} (
                {PgVectorTableSchemeEnums.ID.value} bigserial PRIMARY KEY,
                {PgVectorTableSchemeEnums.TEXT.value} text,
                {PgVectorTableSchemeEnums.VECTOR.value} vector({embedding_size}),
                {PgVectorTableSchemeEnums.METADATA.value} jsonb DEFAULT '{{}}',
                {PgVectorTableSchemeEnums.CHUNK_ID.value} integer,
                FOREIGN KEY ({PgVectorTableSchemeEnums.CHUNK_ID.value}) REFERENCES chunks(chunk_id)
            );""")
            async with self.db_client() as session:
                async with session.begin():
                    await session.execute(stm)
            return True
        return False
    
    
    async def insert_one(self, collection_name: str, text: str, vector: list,
                         metadata: dict = None,
                         record_id: str = None):
        
        if await self.is_collection_existed(collection_name=collection_name):
            if not record_id:
                self.logger.error(f"Can not insert new record without chunk_id: {collection_name}")
                return False
            try:
                stm = sql_text(
                    f"""INSERT INTO {collection_name}
                    ({PgVectorTableSchemeEnums.TEXT.value}, {PgVectorTableSchemeEnums.VECTOR.value}, {PgVectorTableSchemeEnums.METADATA.value}, {PgVectorTableSchemeEnums.CHUNK_ID.value})
                    VALUES (:text, :vector, :metadata, :chunk_id);"""
                    )
                
                metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata is not None else "{}"
                async with self.db_client() as session:
                    async with session.begin():
                        await session.execute(stm,
                                               {
                                                'text': text,
                                                'vector': "[" + ",".join([ str(v) for v in vector ]) + "]",
                                                'metadata': metadata_json,
                                                'chunk_id': record_id
                         })
                        await session.commit()
                        await self.create_vector_index(collection_name=collection_name)

                self.logger.info(f"Inserted new record into collection: {collection_name}")

                return True
            
            except Exception as e:
                self.logger.error(f"Problem while inseting one record: {e}")
                return False
        self.logger.error(f"Can not insert new record to non-existed collection: {collection_name}")

        return False
    

    async def insert_many(self, collection_name: str, texts: list,
                         vectors: list, metadata: list = None,
                         record_ids: list = None, batch_size: int = 50):
        
        if not await self.is_collection_existed(collection_name=collection_name):
            self.logger.error(f"Can not insert new records to non-existed collection: {collection_name}")
            return False
        
        if len(vectors) != len(record_ids):
            self.logger.error(f"Invalid data items for collection: {collection_name}")
            return False
        
        if not metadata or len(metadata) == 0: #to ensure all attribute equals lengths
            metadata = [None] * len(texts)

        
        try:
            async with self.db_client() as session:
                async with session.begin():
                    for i in range(0, len(texts), batch_size):
                        batch_texts = texts[i:i+batch_size]
                        batch_vectors = vectors[i:i + batch_size]
                        batch_metadata = metadata[i:i + batch_size]
                        batch_record_ids = record_ids[i:i + batch_size]

                        values = []

                        for _text, _vector, _metadata, _record_id in zip(batch_texts, batch_vectors, batch_metadata, batch_record_ids):
                            
                            metadata_json = json.dumps(_metadata, ensure_ascii=False) if _metadata is not None else "{}"
                            
                            values.append({
                                'text': _text,
                                'vector': "[" + ",".join([ str(v) for v in _vector ]) + "]",
                                'metadata': metadata_json,
                                'chunk_id': _record_id
                            })
                        
                        batch_insert_sql = sql_text(f'INSERT INTO {collection_name} '
                                        f'({PgVectorTableSchemeEnums.TEXT.value}, '
                                        f'{PgVectorTableSchemeEnums.VECTOR.value}, '
                                        f'{PgVectorTableSchemeEnums.METADATA.value}, '
                                        f'{PgVectorTableSchemeEnums.CHUNK_ID.value}) '
                                        f'VALUES (:text, :vector, :metadata, :chunk_id)')
                        
                        await session.execute(batch_insert_sql, values) 
           
            await self.create_vector_index(collection_name=collection_name)
       
        except Exception as e:
                self.logger.error(f"Problem while inseting many records: {e}")
                return False
        

        return True
    
    async def search_by_vector(self, collection_name: str, vector: list, limit: int):

        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.error(f"Can not search for records in a non-existed collection: {collection_name}")
            return False
        
        vector = "[" + ",".join([ str(v) for v in vector ]) + "]"
        async with self.db_client() as session:
            async with session.begin():
                search_sql = sql_text(f'SELECT {PgVectorTableSchemeEnums.TEXT.value} as text, 1 - ({PgVectorTableSchemeEnums.VECTOR.value} <=> :vector) as score'
                                      f' FROM {collection_name}'
                                      ' ORDER BY score DESC '
                                      f'LIMIT {limit}'
                                      )
                
                result = await session.execute(search_sql, {"vector": vector})

                records = result.fetchall()
                if not records:
                    self.logger.error(f"No records found in collection: {collection_name} for vector search")
                    return []
                self.logger.info(f"Found {len(records)} records in collection: {collection_name} for vector search")
                return [
                    RetrievedDocument(
                        text=record.text,
                        score=record.score
                    )
                    for record in records
                ]