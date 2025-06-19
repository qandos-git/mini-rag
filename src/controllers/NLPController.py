from .BaseController import BaseController
from models.db_schemes import Project, DataChunk
from stores.llm.LLMEnums import DocumentTypeEnum
from stores.llm.templates.template_parser import TemplateParser
import json
from typing import List

class NLPController(BaseController):
    def __init__(self,vectordb_client, embedding_client, generation_client,
                 project: Project):
        super().__init__()

        self.vectordb_client = vectordb_client
        self.embedding_client = embedding_client
        self.generation_client = generation_client

        self.collection_name = self.create_collection_name(project_id=project.project_id)
   
    def create_collection_name(self,project_id:str):
        return f"collection_{self.vectordb_client.default_vector_size}_{project_id}".strip()
    
    async def reset_vector_db_collection(self):
        return await self.vectordb_client.delete_collection(collection_name=self.collection_name)
    
    async def get_vector_db_collection_info(self):
        collection_info = await self.vectordb_client.get_collection_info(collection_name=self.collection_name)

        return json.loads(
            json.dumps(collection_info, default=lambda x: x.__dict__)
        )


    async def index_into_vector_db(self, chunks: List[DataChunk],
                                   chunks_ids: List[int], 
                                   do_reset: bool = False):
        
        #step1 format items
        metadata_list = [c.chunk_metadata for c in chunks]
        texts_list = [c.chunk_text for c in chunks]
        #step2 get embeddings
        vectors_list = self.embedding_client.embed_text(text=texts_list,
                                            document_type=DocumentTypeEnum.DOCUMENT.value)
        '''
        #step3 get collection or create one
        _ = await self.vectordb_client.create_collection(
            collection_name=self.collection_name,
            embedding_size=self.embedding_client.embeddding_size,
            do_reset=do_reset
        )'''
        
        #step4 insert embeddings
        _ = await self.vectordb_client.insert_many(
            collection_name=self.collection_name,
            texts=texts_list,
            vectors=vectors_list,
            metadata=metadata_list,
            record_ids=chunks_ids
        )


        return True
    
    async def search_vector_db_collection(self, text: str, limit: int = 10):

        # step1: get collection name
        query_vector = None

        # step2: get text embedding vector
        vectors = self.embedding_client.embed_text(text=text, 
                                                 document_type=DocumentTypeEnum.QUERY.value)

        if not vectors or len(vectors) == 0:
            return False
        
        if isinstance(vectors, list) and len(vectors) > 0:
            query_vector = vectors[0]

        if not query_vector:
            return False    

        # step3: do semantic search
        results = await self.vectordb_client.search_by_vector(
                collection_name=self.collection_name,
                vector=query_vector,
                limit=limit
            )
        return results
        

    async def answer_rag_question(self,query: str, template_parser, limit: int = 10):
        answer, full_prompt, chat_history = None, None, None
        template_parser = template_parser

        #step1: retrive semantic serch results for user query
        document_chunks = await self.search_vector_db_collection(
            text=query,
            limit=limit
        )

        if not document_chunks:
            return answer, full_prompt,chat_history
        
        #step2: construct the prompt
        system_prompt=template_parser.get("rag","system_prompt")

        document_prompt="\n".join([
            template_parser.get("rag","document_prompt", vars={
                "doc_num":idx+1,
                "chunk_text": self.generation_client.process_text(chunk.text)
            })
            for idx, chunk in enumerate(document_chunks)
            ])
        footer_prompt=template_parser.get("rag","footer_prompt",{"query":query})

        full_prompt = "\n\n".join([document_prompt,footer_prompt])

        chat_history = [self.generation_client.construct_prompt(
            prompt=system_prompt,
            role=self.generation_client.enums.SYSTEM.value
        )]
        #step3: generate the answer
        answer = self.generation_client.generate_text(
            prompt=full_prompt,
            chat_history=chat_history,

        )
        #step4: check answer
        return answer, full_prompt, chat_history