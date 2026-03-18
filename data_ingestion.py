import os
import json
from langchain_community.document_loaders import DirectoryLoader, JSONLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
from langchain_chroma import Chroma

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def data_loading(corpus_path):
    try:
        loader = DirectoryLoader(
            corpus_path,
            glob="**/*.json",
            loader_cls=JSONLoader,
            show_progress=True,
            loader_kwargs={"jq_schema": ".text"},
        )

        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700, 
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
            )
        
        chunks = text_splitter.split_documents(docs)

        
        vector_store = Chroma.from_documents(
            collection_name="Culinary_Knowledge",
            embedding_function=embeddings,
            persist_directory="./Vector_Storage_MasterChef",
        )

        print("The vector store created at {}".format("./Vector_Storage_MasterChef"))
        return True
    
    except Exception as e:
        print(f"An error occurred during data loading: {e}")
        return False

data_loading("./corpus_data")