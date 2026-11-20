from enum import Enum
from dataclasses import dataclass, field
from typing import Any
import time


class MessageType(Enum):
    INITIALIZATION = "Инициализация"
    INIT_MESSAGE = "Инициализация"
    CREATE_ACTOR = "Создание Актора"
    HELLO_WORLD = "Приветствие"
    PRICE_REQUEST = "Запрос цены"
    PRICE_RESPONSE = "Ответ цены"
    PLANNING_REQUEST = "Запрос на размещение"
    PLANNING_RESPONSE = "Ответ на размещение"
    REMOVE_ORDER = "Удаление из расписания"
    DISPLACEMENT_REQUEST = "Запрос на вытеснение"
    DISPLACEMENT_RESPONSE = "Ответ на вытеснение"
    NEW_COURIER = "Новый курьер"
    DELETED_COURIER = "Удаление курьера"
    DELETED_ORDER = "Удаление заказа"
    FREED_SLOT = "Освобождение слота"
    REPLAN_ORDER = "Перепланирование заказа"
    UPDATE_ORDER_PARAMS = "Изменение параметров заказа"
    UPDATE_COURIER_PARAMS = "Изменение параметров курьера"


@dataclass
class Message:
    msg_type: MessageType
    msg_body: Any
    msg_time: float = field(default_factory=time.time)
