#!/bin/bash

# Check if the vector store already exists
if [ -d "./Vector_Storage_MasterChef" ] && [ "$(ls -A ./Vector_Storage_MasterChef)" ]; then
    echo "📂 Vector store found. Skipping ingestion to save time..."
else
    echo "🏗️ No vector store detected. Starting full pipeline (Scrape -> Ingest)..."
    python context_creator.py
fi

echo "🚀 Starting Master Chef API on Port 8000..."
uvicorn main:app --host 0.0.0.0 --port 8000