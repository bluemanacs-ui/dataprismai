from fastapi import APIRouter
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.services.chat_service import generate_mock_chat_response

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/query", response_model=ChatQueryResponse)
def chat_query(payload: ChatQueryRequest) -> ChatQueryResponse:
    return generate_mock_chat_response(payload)
