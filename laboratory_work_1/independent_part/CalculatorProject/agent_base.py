from abc import ABC
from typing import Dict, List, Callable, Any
import logging
import traceback
from thespian.actors import Actor, ActorAddress
from message import MessageType, Message


class AgentBase(ABC, Actor):
    def __init__(self):
        self.name = 'Базовый агент'
        self.handlers: Dict[MessageType, Callable[[Any, ActorAddress], None]] = {}
        self.subscribe(MessageType.HELLO_WORLD, self.handle_hello_world)

    def subscribe(self, msg_type: MessageType, handler: Callable[[Any, ActorAddress], None]):
        if msg_type in self.handlers:
            logging.warning('Повторная подписка на сообщение: %s', msg_type)
        self.handlers[msg_type] = handler

    def receiveMessage(self, msg, sender):
        logging.debug('%s получил сообщение: %s', self.name, msg)

        if isinstance(msg, Message):
            message_type = msg.msg_type
            if message_type in self.handlers:
                try:
                    self.handlers[message_type](msg, sender)
                except Exception as ex:
                    traceback.print_exc()
                    logging.error(ex)
            else:
                logging.warning('%s Отсутствует подписка на сообщение: %s', self.name, message_type)

    def handle_hello_world(self, message, sender):
        print("Hello, world")
