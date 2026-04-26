# 🍜 Master Chef: Agentic AI Culinary Platform

**Master Chef** is an evolving agentic AI platform for culinary intelligence — beginning with a specialized RAG system for East Asian cuisine and expanding into a **multi-agent, multi-modal global cooking assistant**. The system is designed around a **Layered Architecture for Agentic AI**, ensuring modularity, maintainability, and production-readiness as it scales.

> 📖 *The architectural design philosophy powering this platform is documented in the publication: [Layered Architecture for Agentic AI Applications](https://medium.com/@kulvedant24/layered-architecture-for-agentic-ai-applications-eb84f5060400) — Vedant Kulkarni*

---

## 🧭 Platform Vision

What began as a focused RAG system for East Asian cuisine is growing into a **network of specialized culinary agents**, each with domain-specific expertise and modality, coordinated through a shared layered architecture:

| Agent | Role |
| :--- | :--- |
| 🌏 **Cuisine Agents** (×N) | Regional expert agents — East Asian, South Asian, Mediterranean, Latin American, and more — each backed by a domain-specific RAG corpus |
| 🖼️ **Dish Recognition Agent** | Accepts an image of a dish, identifies it using vision models, and retrieves matching recipes and cultural context |
| 👨‍🍳 **Cooking Monitor Agent** | Tracks the cooking process via intermediate image snapshots, gives real-time feedback, and provides **audio guidance** for accessibility |

---

## 🏛️ Layered Architecture

The platform is structured around a **three-layer agentic architecture**, where each layer has a single, clearly scoped responsibility. This decoupling prevents feature bloat, enables independent evolution of each layer, and makes the system resilient to failure at any single point.

```
┌─────────────────────────────────────────────────────────┐
│                     INPUT LAYER                         │
│  Web Scraping · PDF/Image Ingestion · Audio Input       │
│  Chunking · Embedding · Vector Store (ChromaDB)         │
│  MCP Servers for heterogeneous data sources             │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                      AI LAYER                           │
│  Orchestrator Agent · Cuisine Expert Agents             │
│  Dish Recognition Agent · Cooking Monitor Agent         │
│  Hybrid Retrieval (MMR + Similarity) · Reranking        │
│  Two-Pass Verification · Vision + Language Models       │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                    OUTPUT LAYER                         │
│  Structured Recipe Response · Audio TTS Guidance        │
│  Real-time Cooking Feedback · Validation & Grounding    │
│  Agent-to-Agent (A2A) coordination                      │
└─────────────────────────────────────────────────────────┘
```

### Layer 1 — Input Layer

Delivers consistent, pre-processed, LLM-ready inputs to the AI layer. Each agent in the platform operates from its own curated input pipeline:

- **Data Collection:** `BeautifulSoup4`-based recursive scraping from Wikipedia, Wikibooks, and culinary blogs. Domain-specific content extraction strips noise (headers, sidebars, footers) to retain only usable recipe content.
- **Chunking Strategy:** `RecursiveCharacterTextSplitter` at 900-character chunks with 400-character overlap — tuned empirically to preserve the integrity of long-form recipe instructions.
- **Vectorization:** `sentence-transformers/all-MiniLM-L6-v2` for efficient local embedding generation.
- **Vector Store:** **ChromaDB** for lightweight, persistent, SQLite-like vector storage optimized for rapid lookups.
- **Multimodal Ingestion:** For the Dish Recognition and Cooking Monitor agents, the input layer also handles image preprocessing and audio capture.
- **MCP Integration:** Model Context Protocol servers can be plugged into the input layer to connect heterogeneous data sources (cloud storage, specialized culinary databases, live recipe APIs) without disrupting downstream agents.

> *Because input processing is often done offline, data is ready-to-consume before the AI layer is invoked — reducing latency and enabling reuse on downstream failures.*

### Layer 2 — AI Layer

The core intelligence of the platform. Each agent within this layer focuses exclusively on transforming its prepared input into a refined output — no source access, no output formatting concerns.

**Orchestrator Agent**
Routes user queries to the appropriate specialist agent based on intent detection — cuisine lookup, dish recognition, or live cooking assistance.

**Cuisine Expert Agents (×N)**
One agent per regional cuisine, each with its own RAG pipeline:
1. **Hybrid Retrieval:** MMR (5 chunks, λ=0.25) for diversity + similarity search (10 chunks) for precision.
2. **Cross-Encoder Reranking:** `ms-marco-MiniLM-L-6-v2` selects the top 3 chunks to prevent context drowning in smaller models.
3. **Two-Pass Generation:**
   - *Draft Phase:* Qwen 2.5 0.5B generates an initial answer from reranked context.
   - *Verification Phase:* A second LLM call acts as a **Factual Recovery Tool**, auditing the draft against raw context to recover specific details (temperatures, measurements, ratios).

**Dish Recognition Agent**
- Accepts a user-submitted image of a prepared dish.
- Uses a vision-language model to identify the dish, its likely cuisine of origin, and key visible ingredients.
- Hands off the identified dish name to the appropriate Cuisine Expert Agent for full recipe retrieval.

**Cooking Monitor Agent**
- Accepts periodic image snapshots during the cooking process.
- Performs intermediate visual analysis — checking doneness, color, texture, and plating.
- Generates step-by-step **audio guidance** via TTS, supporting users with reading difficulties or hands-free cooking scenarios.

**Agent-to-Agent Communication (A2A)**
Agents coordinate via Google's **A2A framework**, enabling abstracted, standardized inter-agent messaging. This means the Dish Recognition Agent can seamlessly hand off to any Cuisine Expert Agent without tight coupling.

### Layer 3 — Output Layer

Parses, validates, and delivers AI-generated results in the appropriate format for each use case:

- **Structured Recipe Responses:** Formatted with ingredients, steps, and verified measurements.
- **Audio Output:** TTS-rendered cooking instructions streamed to the user in real time.
- **Grounding Validation:** Responses are checked against retrieved context before delivery to ensure faithfulness.
- **Storage:** Results cached for reuse and downstream analytics.

### Optional Auxiliary Layers

The layered model supports plugging in additional cross-cutting layers as the platform matures:

| Layer | Purpose |
| :--- | :--- |
| **Security Layer** | Auth, access control, PII handling |
| **Memory Layer** | User preference caching, session context |
| **Human-in-the-Loop Layer** | Expert chef review for edge-case recipes |
| **Backup Layer** | Pipeline resilience and retry logic |

---

## 📊 Evaluation & Performance (East Asian RAG Agent — Current)

Benchmarked on **200 generated questions**, graded by an LLM-as-a-judge on a 5-point scale:

| Metric | Score (Avg) | Description |
| :--- | :--- | :--- |
| **Correctness** | **3.89** | Accuracy of factual claims |
| **Relevance** | **4.69** | Alignment with user's specific intent |
| **Faithfulness** | **4.42** | Hallucination avoidance |
| **Groundedness** | **4.26** | Answer support from retrieved data |

> *Scores reflect a 0.5B model baseline. Scaling to 7B/13B models or adding stronger Cuisine Expert Agents is expected to significantly improve correctness while maintaining high faithfulness.*

---

## 🗺️ Roadmap

- [x] East Asian Cuisine RAG Agent (v1 — current)
- [ ] Orchestrator Agent with intent routing
- [ ] Additional Cuisine Expert Agents (South Asian, Mediterranean, Latin American)
- [ ] Dish Recognition Agent (vision-language integration)
- [ ] Cooking Monitor Agent (image analysis + TTS audio guidance)
- [ ] A2A inter-agent communication layer
- [ ] MCP server integration for live recipe data sources
- [ ] Memory layer for user preference personalization

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+ (Tested on macOS M1/M4)
- Recommended: Use a virtual environment (`venv` or `conda`)

### Installation

```bash
pip install -r requirements.txt
```

### Running

```bash
python formatted_runner.py
```

- Replace questions in `queries.json` to test custom inputs.
- Optionally use `runner.ipynb` for an interactive notebook experience.

### Rebuilding the Full Pipeline

> ⚠️ Time-consuming — only needed when refreshing the corpus or vector store.

```bash
# Step 1: Clear existing state
rm -rf ./vector_store ./corpus

# Step 2: Re-scrape and re-embed
python context_creator.py

# Step 3: Run inference
python formatted_runner.py
```

---

## 🔬 Architecture References

- **Layered Architecture for Agentic AI** — [medium.com/@kulvedant24](https://medium.com/@kulvedant24/layered-architecture-for-agentic-ai-applications-eb84f5060400)
- **Model Context Protocol (MCP)** — [modelcontextprotocol.io](https://modelcontextprotocol.io/introduction)
- **Google Agent-to-Agent (A2A)** — [github.com/google/A2A](https://github.com/google/A2A)
