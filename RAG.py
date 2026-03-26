import gc
import torch
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from transformers import AutoModelForCausalLM, AutoTokenizer
from sentence_transformers import CrossEncoder

# --- Constants ---
VECTOR_STORE_PATH = "./Vector_Storage_MasterChef"   
SYSTEM_PROMPT = """
Answer the question using ONLY the provided context. 
- If the information is in the context, be direct and try to get answer to the keywords in the query.
- If it's truly not there, say you don't know.

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

def run_model(messages):
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
    
    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=400,
        temperature=0.1,
        do_sample=False,
    )
    
    return tokenizer.batch_decode(
        [out[len(model_inputs.input_ids[0]):] for out in generated_ids],
        skip_special_tokens=True
    )[0].strip()

def get_response(query):

    gc.collect()
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()

    similarity_search_results = vector_store.similarity_search(query, k=10)
    retriever_results = retriever.invoke(query)

    merged_docs = similarity_search_results + retriever_results 
    seen = set()
    unique_merged_docs = []
    for doc in merged_docs:
        text = doc.page_content.strip()
        if text not in seen:
            seen.add(text)
            unique_merged_docs.append(doc)

    pairs = [(query, doc.page_content) for doc in unique_merged_docs]
    scores = reranker.predict(pairs)

    ranked_docs = sorted(zip(unique_merged_docs, scores), key=lambda x: x[1], reverse=True)
    top_docs = [doc for doc, score in ranked_docs[:3]]
    
    sources = {
        doc.metadata.get("cuisine_name", doc.metadata.get("source", "Unknown Source"))
        for doc in top_docs
    }

    # --- Build Context ---
    context_parts = []
    for doc in top_docs:
        title = doc.metadata.get("cuisine_name", "Unknown Title")
        source = doc.metadata.get("source", "Unknown Source")
        content = doc.page_content.strip()
        context_parts.append(f"main topic: {title}\nContent:\n{content}\nSource: {source}")

    context = "\n\n".join(context_parts)

    # --- STAGE 1: Initial Generation ---
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"""
         Answer the question based on the context.
         Question: {query} 
         Context:\n{context}
        Tips:
        -For Ingridients and amount/proprotion based questions search for an Ingridients section, For procedural queries there might be a procedure section.
        -For Info based question search for keywords in query
        """}
    ]
    initial_response = run_model(messages)


    verification_messages = [
            {
                "role": "system", 
                "content": "You are a factual recovery tool. Your ONLY job is to extract missing data from the Context that the Draft Answer missed."
            },
            {
                "role": "user", 
                "content": f"""
        Context: 
        {context}

        Draft Answer: 
        {initial_response}

        User Query: 
        {query}

        CRITICAL TASK:
        1. If the Context contains a more specific answer (numbers, dates, names, temperatures) than the Draft, output the specific answer from the Context.
        2. If the Draft is already perfect, repeat the Draft.
        3. Use ONLY information from the Context. Do not explain your changes.

        Final Answer:"""
            }
        ]
    
    final_response = run_model(verification_messages)

    gc.collect()
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()

    return final_response, set(sources), top_docs