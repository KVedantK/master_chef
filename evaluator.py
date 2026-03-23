import json
import pandas as pd
import os

INPUT_FILE = "sources.json" 

def calculate_metrics_summary(file_path):
    if not os.path.exists(file_path):
        print(f"❌ Error: {file_path} not found!")
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        df = pd.DataFrame(data)

        # 1. DEFINE METRICS
        metrics = ["correctness", "relevance", "faithfulness", "groundedness"]
        existing_metrics = [m for m in metrics if m in df.columns]

        if not existing_metrics:
            print("⚠️ No metric columns found.")
            return

        # 2. FILTER OUT ZERO SCORES (Reframing filter)
        # This removes any rows where correctness is 0
        initial_count = len(df)
        df_filtered = df[df['correctness'] > 0].copy()
        removed_count = initial_count - len(df_filtered)

        if df_filtered.empty:
            print("⚠️ All records had a score of 0. Nothing to calculate.")
            return

        # 3. CALCULATE AVERAGES ON FILTERED DATA
        global_summary = df_filtered[existing_metrics].mean()

        # 4. GROUP BY LEVEL (Handles varied record counts)
        level_summary = None
        record_counts = None
        if 'level' in df_filtered.columns:
            # Standardize casing to avoid "Hard" vs "hard" splitting
            df_filtered['level'] = df_filtered['level'].str.capitalize()
            level_summary = df_filtered.groupby('level')[existing_metrics].mean()
            record_counts = df_filtered['level'].value_counts()

        # 5. CONSOLE OUTPUT
        print("\n" + "="*55)
        print("📊 RAG EVALUATION: CLEANED PERFORMANCE REPORT")
        print("="*55)
        print(f"🧹 Filtered out {removed_count} records with 0 scores.")
        print(f"✅ Analyzing {len(df_filtered)} valid samples.")
        print("-" * 55)
        
        if level_summary is not None:
            print("\n📈 --- PERFORMANCE BY LEVEL (CLEANED) ---")
            print(level_summary.round(2))
            print("\n🔢 --- VALID RECORD COUNTS ---")
            print(record_counts)
            print("-" * 55)

        print("\n🌍 --- GLOBAL AVERAGES (EXCLUDING ZEROS) ---")
        print(global_summary.round(2).to_string())
        print("="*55)

        # 6. SAVE TO FILE
        with open("cleaned_dissertation_results.txt", "w") as f:
            f.write("CLEANED RAG EVALUATION SUMMARY\n")
            f.write(f"Excluded {removed_count} reframed questions.\n")
            if level_summary is not None:
                f.write("\nBY LEVEL:\n" + level_summary.round(2).to_string())
            f.write("\n\nGLOBAL TOTALS:\n" + global_summary.round(2).to_string())
        
        print("\nResults saved to 'cleaned_dissertation_results.txt'")

    except Exception as e:
        print(f"⚠️ An error occurred: {e}")

if __name__ == "__main__":
    calculate_metrics_summary(INPUT_FILE)