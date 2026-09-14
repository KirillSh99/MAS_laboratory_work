from enum import Enum
from dataclasses import dataclass
from typing import Any


class MessageType(Enum):
    INITIALIZATION = 'Инициализация'
    CREATE_ACTOR = 'Создание Актора'
    HELLO_WORLD = 'Приветствие'
    OPERATION = 'Операция'


@dataclass
class Message:
    msg_type: MessageType
    msg_body: Any