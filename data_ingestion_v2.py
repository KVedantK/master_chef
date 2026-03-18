import json
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


def data_loading(corpus_path):
    try:
        docs = []

        print("Reading Files ...\n")
        for file_path in Path(corpus_path).glob("**/*.json"):
            with open(file_path, "r", encoding="utf-8") as f:
                item = json.load(f)

            # Pull metadata from the JSON
            metadata = item.get("metadata", {}).copy()

            # Add useful top-level fields into metadata too
            metadata["url"] = item.get("url")
            metadata["cuisine_name"] = item.get("cuisine_name")
            metadata["source"] = metadata.get("source") or item.get("url") or file_path.name
            metadata["filename"] = metadata.get("filename", file_path.name)

            print("Saved the file: " + metadata["filename"])
            docs.append(
                Document(
                    page_content=item.get("cuisine_name", "") + "\n\n" +item.get("content", ""),
                    metadata=metadata
                )
            )
        
        
        print("Splitting documents into chunks ...\n")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
        )
        print("Chunking the documents ...\n")
        chunks = text_splitter.split_documents(docs)
        print("Ingesting the data to vector store ...\n")
        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            collection_name="Culinary_Knowledge",
            persist_directory="./Vector_Storage_MasterChef",
        )
        print("Collection count immediately after load:", vector_store._collection.count())
        print("*********************************************************")
        print(f"Loaded {len(docs)} documents")
        print(f"Created {len(chunks)} chunks")
        print("The vector store was created at ./Vector_Storage_MasterChef")
        print("*********************************************************")
        return vector_store

    except Exception as e:
        print(f"An error occurred during data loading: {e}")
        return None


data_loading("./corpus_data")
