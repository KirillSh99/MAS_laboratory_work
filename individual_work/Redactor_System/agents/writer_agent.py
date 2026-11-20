import logging
import requests

from thespian.actors import ActorExitRequest

from entities.writer_entity import WriterEntity
from pydantic import BaseModel

from .base_agent import AgentBase
from .messages import Message, MessageType


class GeneratedText(BaseModel):
    text: str


class WriterAgent(AgentBase):
    """Класс агента писатель"""

    def __init__(self):
        super().__init__()
        self.entity: WriterEntity
        self.name = "Агент писателя"

        self.subscribe(MessageType.REQUEST_WRITER_TEXT, self.handle_request_writer_text)

    def handle_init_message(self, message, sender):
        super().handle_init_message(message, sender)

    def ask_llm(self, prompt) -> GeneratedText:
        try:
            r = requests.post(
                "http://ollama:11434/api/generate",
                json={
                    "model": "tinyllama",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            r.raise_for_status()
            raw = r.json().get("response", "")
            return GeneratedText(text=raw)

        except Exception as e:
            logging.error(f"{self.name}: LLM error: {e}")
            return GeneratedText(text="Ошибка генерации Writer!")

    def handle_request_writer_text(self, message, sender):
        request = message.msg_body.get("request")

        if not request:
            logging.warning(f"{self.name}: пустой запрос!")
            return

        logging.info(f"{self.name}: Получил запрос от пользователя: {request}")
        result = self.ask_llm(
            f"Ты профессиональный писатель. Напиши текст по промту: {request}"
        )
        logging.info(f"{self.name}: Получен результат: {result.text}")

        response_message = Message(
            MessageType.RESPONSE_WRITER_TEXT,
            {
                "writer_result": result.text if result else "",
                "agent_type": "EDITOR",
                "prompt": request,
            },
        )
        self.send(self.scene_agent_address, response_message)
