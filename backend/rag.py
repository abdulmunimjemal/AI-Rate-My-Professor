from langchain_pinecone import PineconeVectorStore
from logging import getLogger

logger = getLogger(__name__)

class RAG:
    def __init__(self, pinecone_client, pinecone_index_name, embedding):
        self.pinecone_client = pinecone_client
        self.pinecone_index_name = pinecone_index_name
        self.vector_store = None
        self.embedding = embedding
        self._initialize()

    def _initialize(self):
        if self.pinecone_index_name not in self.pinecone_client.list_indexes():
            raise ValueError(f"Index {self.pinecone_index_name} not found in Pinecone. Please create the index first.")

        index = self.pinecone_client.get_index(self.pinecone_index_name)
        self.vector_store = PineconeVectorStore(index, self.embedding)
        logger.info(f"Vector Store initialized with index {self.pinecone_index_name}")
        
    def lookup(self, query: str, top_k=3):
        self._initialize()
        results = self.vector_store.similarity_search(
            query, top_k=top_k
        )
        return results