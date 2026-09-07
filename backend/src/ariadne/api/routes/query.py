from fastapi import APIRouter, Depends

from ariadne.api.deps import get_reasoning_engine
from ariadne.rag.reasoning import ReasoningEngine
from ariadne.schemas import QueryRequest, QueryResult

router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query")
def query(body: QueryRequest, engine: ReasoningEngine = Depends(get_reasoning_engine)) -> QueryResult:
    return engine.answer_query(body.query)
