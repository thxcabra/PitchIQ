"""View 4: the conversational endpoint. NLU -> executor -> structured response."""
from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.chat.executor import ChatExecutor
from app.deps import Services, get_services
from app.models.responses import ChatResponse
from app.nlu.interpreter import Interpreter

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)


@lru_cache(maxsize=1)
def get_interpreter() -> Interpreter:
    return Interpreter()


@router.post("/chat", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    svc: Services = Depends(get_services),
    interpreter: Interpreter = Depends(get_interpreter),
):
    structured = interpreter.interpret(req.message)
    return ChatExecutor(svc).execute(structured)
