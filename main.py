from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from RAG import *

# --- Configuration & Setup ---
app = FastAPI(title="Master Chef East Asian Culinary API")

# --- Request/Response Schemas ---
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: list[dict]

# --- API Endpoints ---

@app.post("/ask-chef", response_model=QueryResponse)
async def get_culinary_answer(request: QueryRequest):
    query = request.query
    try:
        response, sources, docs = get_response(query)

        return QueryResponse(
            query=query,
            answer=response,
            sources=[{"source": src} for src in sources]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

