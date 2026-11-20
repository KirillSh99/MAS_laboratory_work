import logging
import traceback
from abc import ABC
from typing import Any, Callable, Dict

from thespian.actors import Actor, ActorAddress, ActorExitRequest, ChildActorExited
from .messages import Message, MessageType


class AgentBase(ABC, Actor):
    """Базовая реализация агента"""

    def __init__(self):
        self.name = "Базовый агент"
        super().__init__()
        self.handlers: Dict[MessageType, Callable[[Any, ActorAddress], None]] = {}
        self.scene_agent_address = None
        self.dispatcher = None
        self.entity = None
        self.subscribe(MessageType.INIT_MESSAGE, self.handle_init_message)

    def subscribe(
        self, msg_type: MessageType, handler: Callable[[Any, ActorAddress], None]
    ):
        if msg_type in self.handlers:
            logging.warning("Повторная подписка на сообщение: %s", msg_type)
        self.handlers[msg_type] = handler

    def handle_delete_message(self):
        """
        Обработчик сообщения об удалении сущности.
        :return:
        """
        logging.info(f"{self} получил сообщение - ActorExitRequest")
        self.entity.is_deleting = True

    def receiveMessage(self, msg, sender):
        """Обрабатывает сообщения - запускает их обработку в зависимости от типа.
        :param msg:
        :param sender:
        :return:
        """
        logging.debug("%s получил сообщение: %s", self.name, msg)
        if isinstance(msg, ActorExitRequest):
            self.handle_delete_message()
            return

        if isinstance(msg, ChildActorExited):
            logging.info(
                "%s — дочерний актор завершён: %s",
                self.name,
                msg.childAddress,
            )
            return

        if isinstance(msg, Message):
            message_type = msg.msg_type
            if message_type in self.handlers:
                try:
                    # logging.info(f'{self} получил сообщение {msg}')
                    self.handlers[message_type](msg, sender)
                except Exception as ex:
                    traceback.print_exc()
                    logging.error(ex)
            else:
                logging.warning(
                    "%s Отсутствует подписка на сообщение: %s", self.name, message_type
                )
            return
        else:
            logging.error("%s Неверный формат сообщения: %s", self.name, msg)
            return

    def __str__(self):
        return self.name

    def handle_init_message(self, message, sender):
        message_data = message.msg_body
        self.scene_agent_address = message_data.get("scene_agent_address")
        self.dispatcher = message_data.get("dispatcher")
        self.entity = message_data.get("entity")
        self.name = self.name + " " + self.entity.name
        logging.info(f"{self} проинициализирован")