import re
import logging
import requests

from thespian.actors import ActorExitRequest

from entities.expert_entity import ExpertEntity
from pydantic import BaseModel

from .base_agent import AgentBase
from .messages import Message, MessageType


class Score(BaseModel):
    score: int


class ExpertAgent(AgentBase):
    """Класс агента эксперта"""

    def __init__(self):
        super().__init__()
        self.entity: ExpertEntity
        self.name = "Агент эксперта"

        self.subscribe(MessageType.REQUEST_EXPERT_SCORE, self.handle_request_expert_score)

    def handle_init_message(self, message, sender):
        super().handle_init_message(message, sender)

    def ask_llm(self, prompt) -> Score:
        try:
            r = requests.post(
                "http://ollama:11434/api/generate",
                json={
                    "model": "tinyllama",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3
                    }
                },
                timeout=60
            )

            r.raise_for_status()

            raw = r.json().get("response", "").strip()

            match = re.search(r"\d+", raw)
            if match:
                score = int(match.group())
                score = max(1, min(score, 5))
            else:
                score = 0

            return Score(score=score)

        except Exception as e:
            logging.error(f"{self.name}: LLM error: {e}")
            return Score(score=0)

    def handle_request_expert_score(self, message, sender):
        text = message.msg_body.get("text")
        prompt = message.msg_body.get("prompt")

        if not text:
            logging.warning(f"{self.name}: пустой текст!")
            return

        logging.info(f"{self}: Получил текст от агента сцены")
        llm_prompt = f"""
                Ты профессиональный эксперт.
        
                Оцени текст по шкале от 1 до 5.
        
                Правила:
                - 1 = очень плохо
                - 5 = отлично
                - верни ТОЛЬКО число
        
                Промт пользователя:
                {prompt}
        
                Текст:
                {text}
        """

        result = self.ask_llm(llm_prompt)
        logging.info(f"{self.name}: Оценка: {result.score}")

        response_message = Message(
            MessageType.RESPONSE_EXPERT_SCORE,
            {
                "expert_result": result.score,
                "editor_result": text,
            },
        )
        self.send(self.scene_agent_address, response_message)

