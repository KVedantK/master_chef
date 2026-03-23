import json
import os
from tqdm import tqdm
from RAG import get_response 

INPUT_FILE = "benchmark_dataset_v2.json"
OUTPUT_FILE = "rag_results_2.json"
def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ {INPUT_FILE} not found!")
        return

    # 1. Load the Benchmark (New and Old questions)
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    # 2. Load Existing Results (to see what we already did)
    rag_results = []
    completed_questions = set()
    
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            try:
                rag_results = json.load(f)
                # Store the actual question strings in a set for O(1) lookup
                completed_questions = {item["question"] for item in rag_results}
                print(f"📝 Found {len(completed_questions)} existing answers. Skipping those...")
            except json.JSONDecodeError:
                print("⚠️ Output file was empty or corrupted. Starting fresh.")
                rag_results = []

    print(f"🚀 Running RAG on remaining questions...")

    # 3. Filter the dataset to only include new questions
    new_questions = [item for item in dataset if item.get("question") not in completed_questions]

    if not new_questions:
        print("✅ All questions in the benchmark have already been processed!")
        return

    for item in tqdm(new_questions):
        question = item.get("question")
        gold = item.get("gold_answer") or item.get("answer")

        try:
            student_answer, sources, top_docs = get_response(question)

            serializable_docs = []
            if top_docs:
                for doc in top_docs:
                    serializable_docs.append({
                        "page_content": getattr(doc, 'page_content', str(doc)),
                        "metadata": getattr(doc, 'metadata', {})
                    })

            rag_results.append({
                "question": question,
                "gold_answer": gold,
                "rag_answer": student_answer,
                "sources_used": list(sources) if sources else [],
                "retrieved_context": serializable_docs 
            })

            # Save incrementally after EVERY question (Safety for your 3-day deadline!)
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(rag_results, f, indent=4, ensure_ascii=False)

        except Exception as e:
            print(f"\n⚠️ Error on question: {question[:30]}... | {e}")
            continue

    print(f"\n✅ Done! Total results in {OUTPUT_FILE}: {len(rag_results)}")

if __name__ == "__main__":
    main()