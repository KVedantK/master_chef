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
You are a precise and reliable assistant for question answering using retrieved context on East Asian cuisine.

You must follow these rules strictly:

1. SOURCE OF TRUTH
- Use ONLY the provided context to answer.
- Do NOT use prior knowledge.
- If the answer is not present or cannot be derived from the context, say:
  "I don’t know based on the provided context."

2. DERIVED ANSWERS (IMPORTANT)
- If the answer requires simple reasoning or transformation (e.g., math, unit conversion, aggregation, comparison),
  you MUST compute it using the context.
- Do not include explanantions for this in final answer be accurate in calculations
- Always prefer a derived correct answer over copying incomplete information.

3. ACCURACY OVER COPYING
- Do NOT blindly copy text from context.
- Ensure the answer directly matches the user’s question.
- If context gives related but incomplete data, transform it to fully answer the question.

4. MULTIPLE SOURCES
- If multiple pieces of context are relevant, combine them carefully.
- Resolve conflicts by prioritizing the most explicit or detailed information.

5. NO HALLUCINATION
- Do NOT guess or assume missing values.
- If a key value is missing, say you don’t know.

6. ANSWER STYLE
- Be clear and concise.
- Include reasoning steps ONLY when calculation or transformation is required.
- Always include a short citation or reference from the context (e.g., source, title, or snippet).

7. FORMAT
Final Answer:
<your answer>

Source:
<reference from context>

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
    search_kwargs={'k':5, 'fetch_k': 20, 'lambda_mult': 0.5}
)

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def get_response(query):

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
        {"role": "system", "content": SYSTEM_PROMPT},
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

    return response.strip(), set(sources)