import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import RequestHistory
from schemas import UserRequest, AgentResponse
from redis_cache import redis_client
from thespian.actors import ActorSystem
from messages import Message, MessageType

router = APIRouter(prefix="/agents", tags=["Agents"])

@router.post("/generate", response_model=AgentResponse)
def generate_text(req: UserRequest, request: Request, db: Session = Depends(get_db)):
    cached = redis_client.get(req.prompt)
    if cached:
        return json.loads(cached)

    dispatcher = request.app.state.dispatcher
    system = ActorSystem() # Подключаемся к запущенной системе

    try:
        raw_result = system.ask(dispatcher, Message(
            MessageType.REQUEST_USER,
            {"request_user": req.prompt}
        ), timeout=60)

        if not raw_result:
            raise HTTPException(status_code=504, detail="Превышено время ожидания агентов")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка ActorSystem: {str(e)}")

    new_history = RequestHistory(
        prompt=req.prompt,
        result=raw_result
    )
    db.add(new_history)
    db.commit()
    redis_client.set(req.prompt, json.dumps(raw_result), ex=3600)

    return raw_result