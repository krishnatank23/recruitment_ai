#vectore store
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# class VectorStore:
#     def __init__(self):
#         self.embedding_model = HuggingFaceEmbeddings(
#             model_name="sentence-transformers/all-MiniLM-L6-v2"
#         )
#         self.db = FAISS.from_texts(["init"], self.embedding_model)

#     def add(self, texts, metadatas):
#         self.db.add_texts(texts=texts, metadatas=metadatas)

#     def search(self, query, k=5):
#         return self.db.similarity_search_with_score(query, k)
class VectorStore:
    def __init__(self):
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.db = None

    def add(self, texts, metadatas):
        if self.db is None:
            self.db = FAISS.from_texts(texts, self.embedding_model, metadatas)
        else:
            self.db.add_texts(texts, metadatas)

    def search(self, query, k=5):
        return self.db.similarity_search_with_score(query, k)
