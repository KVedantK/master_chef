import os
import json
from langchain_community.document_loaders import DirectoryLoader, JSONLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

load_dotenv()

def run_hosted_ingestion():
    loader = DirectoryLoader(
        './corpus_data',
        glob='**/*.json',
        loader_cls=JSONLoader,
        loader_kwargs={'jq_schema': '.content', 'text_content': True}
    )

    print("Loading documents from json to Docuement format")
    docs = loader.load()

    # CHUNKING
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = text_splitter.split_documents(docs)
    print(f"Created {len(chunks)} chunks.")

    # 3. Vectorization with of the generated chunks using HuggingFace's API
    embeddings = HuggingFaceEmbeddings(
        api_key=os.getenv("HF_API_KEY"), 
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    print("🧬 Fetching embeddings from Hosted API and building FAISS index...")
    # This might take a moment depending on network speed
    vector_db = FAISS.from_documents(chunks, embeddings)

    # 4. Save the Index
    # Even with hosted embeddings, we save the resulting vectors locally
    # so the demo doesn't need to re-call the API for every query.
    vector_db.save_local("faiss_index_hosted")
    print("✅ Ingestion Complete. Index saved to 'faiss_index_hosted'.")

run_hosted_ingestion()