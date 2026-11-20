from dataclasses import dataclass
from enum import Enum
from typing import Any


class MessageType(Enum):
    INIT_MESSAGE = "Инициализация"
    INIT_DISPATCHER = "Инициализация диспетчера"
    REGISTER_DISPATCHER = "Регистрация диспетчера в сцене"
    UPDATE_ENTITY_MESSAGE = "Регистрация агента в сцене"
    REQUEST_USER = "Запрос от пользователя"
    REQUEST_USER_SCENE = "Запрос пользователя в сцену"
    REQUEST_WRITER_TEXT = "Запрос агенту Писателю на создание текста"
    REQUEST_EDITOR_TEXT = "Запрос агенту Проверяющему на редактирование текста"
    REQUEST_EXPERT_SCORE = "Запрос агенту Эксперту на оценку текста"
    RESPONSE_WRITER_TEXT = "Ответ сцене от агента Писателя"
    RESPONSE_EDITOR_TEXT = "Ответ сцене от агента Проверяющего"
    RESPONSE_EXPERT_SCORE = "Ответ сцене от агента Эксперта"
    CLEAN_DATA = "Запрос на очистку данных"


@dataclass
class Message:
    """Класс для хранения сообщений"""

    msg_type: MessageType
    msg_body: Any