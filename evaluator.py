import json
import pandas as pd
import os

INPUT_FILE = "new_eval.json"

def calculate_simple_averages(file_path):
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    metrics = ["correctness", "relevance", "faithfulness", "groundedness"]
    
    existing_metrics = [m for m in metrics if m in df.columns]

    if not existing_metrics:
        print("No metric columns found in the JSON file.")
        return

    averages = df[existing_metrics].mean()
    
    print("--- RAG Evaluation Averages ---")
    print(averages.to_string())
    print(f"\nTotal records processed: {len(df)}")

calculate_simple_averages(INPUT_FILE)