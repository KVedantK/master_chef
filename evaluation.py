import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

load_dotenv()

llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0.3,
    groq_api_key=os.getenv("GROQ_API_KEY").strip() if os.getenv("GROQ_API_KEY") else None
)

CORPUS_DIR = "./corpus_data"
OUTPUT_FILE = "benchmark_dataset.json"
PROGRESS_FILE = "processed_files.txt"


DELAY_SECONDS = 2 


prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a culinary expert. Based on the text, generate exactly 3 question-answer pairs.
    Structure the response as a JSON list with exactly these keys: "level", "question", "gold_answer".
    
    Levels:
    - Easy: Direct fact lookup.
    - Medium: Requires connecting two points or explaining a process.
    - Hard: Requires inference or reasoning about the cultural/historical context.
    
    Format:
    [
      {{ "level": "Easy", "question": "...", "gold_answer": "..." }},
      {{ "level": "Medium", "question": "...", "gold_answer": "..." }},
      {{ "level": "Hard", "question": "...", "gold_answer": "..." }}
    ]"""),
    ("user", "Text Content:\n{content}\n\nSource: {filename}")
])

def generate_benchmark():
    all_questions = []
    processed_files = set()

    # Load progress
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            processed_files = set(line.strip() for line in f)

    # Load existing data to append
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            try:
                all_questions = json.load(f)
            except json.JSONDecodeError:
                all_questions = []

    json_files = [f for f in Path(CORPUS_DIR).glob("*.json") if f.name not in processed_files]
    
    print(f"Starting generation for {len(json_files)} files...")

    # Set up the chain
    chain = prompt | llm | JsonOutputParser()

    for file_path in tqdm(json_files):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                content = data.get("content", "")

            if not content or len(content) < 100:
                continue

            # Run the chain
            file_questions = chain.invoke({"content": content, "filename": file_path.name})

            # Add metadata
            for q in file_questions:
                q["source_file"] = file_path.name
                all_questions.append(q)

            # Update progress & Save file
            with open(PROGRESS_FILE, "a") as pf:
                pf.write(f"{file_path.name}\n")
            
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(all_questions, f, indent=4, ensure_ascii=False)

            time.sleep(DELAY_SECONDS)

        except Exception as e:
            print(f"there was an error {e} continuing the next file")
            continue

    print(f"\nTotal questions in {OUTPUT_FILE}: {len(all_questions)}")

if __name__ == "__main__":
    generate_benchmark()