from enum import Enum
from dataclasses import dataclass
from typing import Any


class MessageType(Enum):
    INITIALIZATION = 'Инициализация'
    CREATE_ACTOR = 'Создание Актора'
    HELLO_WORLD = 'Приветствие'
    SEND_MESSAGE = 'Отправка сообщения'
    GET_RESULT = 'Получение кол-во сообщений от агента TimeAgent'
    SEND_COUNT_MESSAGE_OF_SendAgent = "Отпратвка агенту SendAgent кол-во обращений"
    COUNT_SEND_MESSAGE = 'Принятие кол-ва сообщений'


@dataclass
class Message:
    msg_type: MessageType
    msg_body: Any
