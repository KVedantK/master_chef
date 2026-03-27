# Master Chef: AI Culinary Assistant

**Master Chef** is a specialized RAG (Retrieval-Augmented Generation) system designed to provide highly accurate, grounded culinary information from open-source East Asian cooking data. By leveraging a localized, two-stage verification pipeline, it ensures factual reliability even when using small-parameter models like Qwen-2.5 0.5B.

---

## System Architecture

### 1. Data Collection & Scraping
Our data pipeline is built for high-precision extraction from diverse web sources including Wikipedia, Wikibooks, and specialized culinary blogs.

* **Recursive Discovery:** Utilizes `BeautifulSoup4` to traverse nested category trees and generate a comprehensive corpus of individual recipe links.
* **Targeted Extraction:** Implements domain-specific scraping logic. The system identifies primary content containers (e.g., MediaWiki's `bodyContent`) while stripping noise like headers, footers, and sidebars.
* **Anti-Blocking:** Employs custom User-Agent headers (`Master-Chef-App-v1`) to navigate server-side rate-limiting and bot-detection.
* **Format:** Standardizes unstructured web data into structured JSON objects containing content and metadata (source, title, category).

### 2. Data Ingestion & Vectorization
* **Chunking Strategy:** Uses a `RecursiveCharacterTextSplitter` with a **900-character chunk size**. 
    * *Note:* Through iterative testing (450, 600), 900 was identified as the optimal size to maintain the integrity of long-form recipe instructions which often appear fragmented in smaller windows.
* **Contextual Overlap:** A **400-character overlap** ensures semantic continuity between chunks, preventing the loss of procedural steps.
* **Embeddings:** Powered by `sentence-transformers/all-MiniLM-L6-v2` for efficient, high-quality local vector generation.
* **Vector Store:** **ChromaDB** is used for local persistence, offering an SQLite-like lightweight architecture for rapid lookups and compact storage on disk.

### 3. Inference Pipeline (Two-Pass Verification)
To overcome the limitations of small-scale models (0.5B), we implemented a sophisticated multi-stage retrieval and synthesis process:

1.  **Hybrid Retrieval:** * **MMR (Maximal Marginal Relevance):** Fetches 5 chunks with a diversity factor ($\lambda = 0.25$) to ensure a broad context.
    * **Similarity Search:** Fetches 10 chunks based on vector distance.
2.  **Cross-Encoder Reranking:** All candidates are processed through a `CrossEncoder` (`ms-marco-MiniLM-L-6-v2`). Only the **top 3 chunks** are selected to prevent "context drowning" in the 0.5B model.
3.  **Two-Pass Generation:**
    * **Draft Phase:** Qwen 2.5 0.5B generates an initial response based on the reranked context.
    * **Verification Phase:** A second LLM call acts as a **"Factual Recovery Tool."** It audits the draft against the raw context to recover specific missing data (e.g., temperatures, exact measurements, or specific ingredient ratios).

---

## 📊 Evaluation & Performance
The system was benchmarked against a set of **200 generated questions**, with responses graded by an LLM-as-a-judge (GPT-4o/5.4 equivalent) on a 5-point scale.

| Metric | Score (Avg) | Description |
| :--- | :--- | :--- |
| **Correctness** | **3.89** | Accuracy of the factual claims. |
| **Relevance** | **4.69** | Alignment with the user's specific intent. |
| **Faithfulness** | **4.42** | Avoiding hallucinations (sticking to context). |
| **Groundedness** | **4.26** | Extent to which answer is supported by retrieved data. |

> *Note: These scores reflect the performance of a 0.5B model; results are expected to improve significantly if scaled to 7B or 13B models.*

---

## 🚀 Quick Start

### Prerequisites
* Python 3.10+ (Tested on macOS M1/M4)
* Recommended: Use a virtual environment (`venv` or `conda`)

### Installation
```bash
pip install -r requirements.txt
```
### Running
```bash
python formatted_runner.py
```
- replace the questions in the `queries.json`

### To test the full pipeline (not suggested as a bit time consuming)
Delete the vector store 
Delete the corpus folder
```
python context_creator.py
python formatted_runner.py
```
