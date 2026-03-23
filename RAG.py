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

## Contants:

VECTOR_STORE_PATH = "./Vector_Storage_MasterChef"   
SYSTEM_PROMPT = """
You are a helpful Culinary Assistant assigned with task to answer queries regarding east asian cuisine.
You are provided all the knowledge required to answer the query.

- Answer the query based on knowledge in the context only.
- If answer is not found in the context say 'I dont know the answer'
- Do not miss on the facts in context that matches the main topic of the query
- Read the full context before generating the answer
- Be ready to get confusing questions using synonym terms that may be in the context feel free to match such semantically and answer

Some Tone instructions:
- Be precise and to the point do not include unwanted noise like chattering in the response.
- Once ready phrase the answer like you are answering a human being addressing their query
- NEVER AT ALL MAKE UP AN ANSWER its okay to say you dont know or to reply something based on the context but not to make up an answer
Some Tips:
- For questions asking what is used, Which Oil / sauce / fruit / vegetable / meat is used -- refer the ingridients in the context.
- For questions asking procedures, receipe look for procedures in the context.
- For fact based question check the direct answer first in the context else go to derive it.

Output format:
Final Answer: <answer>
Source: <source name>

"""

model_name = "Qwen/Qwen2.5-0.5B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"
)

vector_store = Chroma(
    collection_name="Culinary_Knowledge",
    embedding_function=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"),
    persist_directory=VECTOR_STORE_PATH
)

retriever = vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={'k':5, 'fetch_k' : 20, 'lambda_mult' : 0.25}
)

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def get_response(query):

    similarity_search_results = vector_store.similarity_search(query, k=10)
    retriever_results = retriever.invoke(query)

    merged_docs = similarity_search_results + retriever_results  # Combine both retrievals for richer context
    seen = set()
    unique_merged_docs = []
    for doc in merged_docs:
        text = doc.page_content.strip()
        if text not in seen:
            seen.add(text)
            unique_merged_docs.append(doc)

    pairs = [(query, doc.page_content) for doc in unique_merged_docs]
    scores = reranker.predict(pairs)

    ranked_docs = sorted(
        zip(unique_merged_docs, scores),
        key=lambda x: x[1],
        reverse=True
    )

    top_docs = [doc for doc, score in ranked_docs[:3]]
    sources = {
        doc.metadata.get("cuisine_name", doc.metadata.get("source", "Unknown Source"))
        for doc in top_docs
    }
    context_parts = []
    for i, doc in enumerate(top_docs, 1):
        title = doc.metadata.get("cuisine_name", "Unknown Title")
        source = doc.metadata.get("source", "Unknown Source")
        content = doc.page_content.strip()

        context_parts.append(
            f"main topic: {title}\n"
            f"Content:\n{content}"
            f"Source: {source}\n"
        )

    context = "\n\n".join(context_parts)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"""Question: {query} 
         Context:\n{context} 
         Once you are ready with answer check if it answers the query, if yes then respond if not just try going through again"""}
    ]
    
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)


    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=500,
        temperature=0.1,
        do_sample = True,
    )
    
    response = tokenizer.batch_decode(
        [out[len(in_ids):] for in_ids, out in zip(model_inputs.input_ids, generated_ids)],
        skip_special_tokens=True
    )[0]
    return response.strip(), set(sources), top_docs