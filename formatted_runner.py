import json
import os
import torch
import gc
from tqdm import tqdm

from RAG import get_response 

INPUT_FILE = "queries.json"
OUTPUT_FILE = "formatted_outcome.json"

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ {INPUT_FILE} not found!")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        input_data = json.load(f)

    queries = input_data.get("queries", [])
    results = []

    print(f"🚀 Running RAG on {len(queries)} benchmark queries...")

    for item in tqdm(queries):
        query_id = item.get("query_id")
        query_text = item.get("query")

        try:
            # 1. Get response from your RAG function
            # response: str, sources: set, top_docs: List[Document]
            response_text, sources, top_docs = get_response(query_text)

            # 2. Format retrieved context to match the benchmark requirement
            # We use an index or hash for doc_id since Chroma metadata usually 
            # provides the filename/source rather than a numeric ID.
            formatted_context = []
            for i, doc in enumerate(top_docs):
                formatted_context.append({
                    "doc_id": f"{i:03d}", # Formats as 000, 001, etc.
                    "text": doc.page_content.strip()
                })

            # 3. Build the specific output object
            results.append({
                "query_id": query_id,
                "query": query_text,
                "response": response_text,
                "retrieved_context": formatted_context
            })

        except Exception as e:
            print(f"\n⚠️ Error on query_id {query_id}: {e}")
            # Append a failure response to keep the JSON structure intact
            results.append({
                "query_id": query_id,
                "query": query_text,
                "response": "I dont know the answer (Error occurred)",
                "retrieved_context": []
            })
            continue

    # 4. Final output structure
    output_data = {"results": results}

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Done! Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()