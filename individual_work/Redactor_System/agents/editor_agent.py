import logging
import requests

from thespian.actors import ActorExitRequest

from entities.editor_entity import EditorEntity
from pydantic import BaseModel

from .base_agent import AgentBase
from .messages import Message, MessageType


class EditorText(BaseModel):
    text: str


class EditorAgent(AgentBase):
    """Класс агента проверяющего"""

    def __init__(self):
        super().__init__()
        self.entity: EditorEntity
        self.name = "Агент проверяющего"

        self.subscribe(MessageType.REQUEST_EDITOR_TEXT, self.handle_request_editor_text)

    def handle_init_message(self, message, sender):
        super().handle_init_message(message, sender)

    def ask_llm(self, prompt) -> EditorText:
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
            return EditorText(text=raw)

        except Exception as e:
            logging.error(f"{self.name}: LLM error: {e}")
            return EditorText(text="Ошибка генерации Editor!")

    def handle_request_editor_text(self, message, sender):
        text = message.msg_body.get("text")
        prompt = message.msg_body.get("prompt")

        if not text:
            logging.warning(f"{self.name}: пустой текст!")
            return

        logging.info(f"{self.name}: Получил текст от агента сцены")
        llm_prompt = f"""
                Ты профессиональный редактор.
        
                Задача:
                - исправь орфографические ошибки
                - исправь логические ошибки
                - улучши читаемость текста
                - НЕ меняй смысл
                
                Верни только исправленный текст.
                
                Промт пользователя:
                {prompt}
                
                Текст:
                {text}
        """

        result = self.ask_llm(llm_prompt)

        new_text = result.text.strip()
        logging.info(f"{self}: Получен результат: {new_text}")
        response_message = Message(
            MessageType.RESPONSE_EDITOR_TEXT,
            {
                "editor_result": new_text,
                "agent_type": "EXPERT",
                "prompt": prompt
            },
        )
        self.send(self.scene_agent_address, response_message)
