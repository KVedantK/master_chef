import json
import os
import gc
from tqdm import tqdm
from RAG import get_response 

INPUT_FILE = "queries.json"
OUTPUT_FILE = "formatted_outcome.json"

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"{INPUT_FILE} not found!")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        input_data = json.load(f)

    queries = input_data.get("queries", [])
    results = []

    print(f"Running RAG on {len(queries)} test queries...")

    for item in tqdm(queries):
        query_id = item.get("query_id")
        query_text = item.get("query")

        try:
            response_text, sources, top_docs = get_response(query_text)

            formatted_context = []
            for i, doc in enumerate(top_docs):
                formatted_context.append({
                    "doc_id": f"{i:03d}",
                    "text": doc.page_content.strip()
                })

            results.append({
                "query_id": query_id,
                "query": query_text,
                "response": response_text,
                "retrieved_context": formatted_context
            })
            
            gc.collect()

        except Exception as e:
            print(f"\nError on query_id {query_id}: {e}")
            results.append({
                "query_id": query_id,
                "query": query_text,
                "response": "I dont know the answer (Error occurred)",
                "retrieved_context": []
            })
            gc.collect()
            continue

    # 4. Final output structure
    output_data = {"results": results}

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to {OUTPUT_FILE}")


main()