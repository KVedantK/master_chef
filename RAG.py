import os
import json
from langchain_community.document_loaders import DirectoryLoader, JSONLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv
from langchain_chroma import Chroma
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from sentence_transformers import CrossEncoder

model_name = "Qwen/Qwen2.5-0.5B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"
)

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def get_response(query, vector_store_path):

    vector_store = Chroma(
        collection_name="Culinary_Knowledge",
        embedding_function=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"),
        persist_directory=vector_store_path
    )

    retriever = vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={'k':5, 'fetch_k': 20, 'lambda_mult': 0.5}
    )

    similarity_search_results = vector_store.similarity_search(query, k=5)
    retriever_results = retriever.invoke(query)


    merged_docs = similarity_search_results + retriever_results  # Combine both retrievals for richer context
    seen = set()
    unique_merged_docs = []
    for doc in merged_docs:
        text = doc.page_content.strip()
        if text not in seen:
            seen.add(text)
            unique_merged_docs.append(doc)
    sources = [doc.metadata.get("source", "Unknown Source") for doc in unique_merged_docs]
    pairs = [(query, doc.page_content) for doc in unique_merged_docs]
    scores = reranker.predict(pairs)

    ranked_docs = sorted(
        zip(unique_merged_docs, scores),
        key=lambda x: x[1],
        reverse=True
    )

    top_docs = [doc for doc, score in ranked_docs[:5]]
    context = "\n\n".join([doc.page_content for doc in top_docs])
    messages = [
        {"role": "system", "content": "You are a specialist East Asian Master Chef. Use the provided context to answer the user's question accurately and verbosely if there are any explanations. Answer what is asked in the query no additional context to be included.If the answer is not in the context, say you don't know based on the current records. Be concise. make sure you include the source of the information"},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
    ]
    

    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)


    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=512,
        temperature=0.1 
    )
    
    response = tokenizer.batch_decode(
        [out[len(in_ids):] for in_ids, out in zip(model_inputs.input_ids, generated_ids)],
        skip_special_tokens=True
    )[0]

    return response.strip(), sources



print(get_response("What foods were introduced to Korea through the Mongol invasion of Goryeo?", "./Vector_Storage_MasterChef"))